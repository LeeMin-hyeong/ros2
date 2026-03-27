import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from smart_shop_interfaces.srv import (
    PlaceOrder,
    CheckStock,
    AuthorizePayment,
    DiscountApply,
)


class OrderManager(Node):
    def __init__(self):
        super().__init__('order_manager')

        # 재진입 허용 콜백 그룹
        self.cb_group = ReentrantCallbackGroup()

        # PlaceOrder 서비스 서버
        self.srv = self.create_service(
            PlaceOrder,
            'place_order',
            self.cb_place_order,
            callback_group=self.cb_group
        )

        # 내부 서비스 클라이언트
        self.stock_cli = self.create_client(
            CheckStock,
            'check_stock',
            callback_group=self.cb_group
        )
        self.pay_cli = self.create_client(
            AuthorizePayment,
            'authorize_payment',
            callback_group=self.cb_group
        )
        self.discount_cli = self.create_client(
            DiscountApply,
            'discount_apply',
            callback_group=self.cb_group
        )

        self.get_logger().info("OrderManager ready (SYNC, safe).")

    def wait_service_or_fail(self, client, name, timeout_sec=3.0):
        if not client.wait_for_service(timeout_sec=timeout_sec):
            self.get_logger().error(f"Service not available: {name}")
            return False
        return True
    
    def cb_place_order(self, request, response):
        # 주문 수신 로그
        self.get_logger().info(
            f"Order received: order_id={request.order_id}, "
            f"item={request.item_id}, qty={request.quantity}, "
            f"amount={request.amount} {request.currency}"
        )

        # 재고 서비스 확인
        if not self.wait_service_or_fail(self.stock_cli, 'check_stock'):
            self.get_logger().error("check_stock service unavailable")

            response.success = False
            response.status = "dependency_unavailable"
            response.detail = "check_stock not available"
            response.remaining_stock = 0
            response.payment_auth_code = ""
            return response

        # 결제 서비스 확인
        if not self.wait_service_or_fail(self.pay_cli, 'authorize_payment'):
            self.get_logger().error("authorize_payment service unavailable")

            response.success = False
            response.status = "dependency_unavailable"
            response.detail = "authorize_payment not available"
            response.remaining_stock = 0
            response.payment_auth_code = ""
            return response
        
        if not self.wait_service_or_fail(self.discount_cli, 'discount_apply'):
            self.get_logger().error("discount_apply service unavailable")

            response.success = False
            response.status = "dependency_unavailable"
            response.detail = "discount_apply not available"
            response.remaining_stock = 0
            response.payment_auth_code = ""
            return response

        # 재고 확인
        stock_req = CheckStock.Request()
        stock_req.item_id = request.item_id
        stock_req.quantity = request.quantity

        stock_res = self.stock_cli.call(stock_req)

        if not stock_res.available:
            self.get_logger().warn(
                f"Order rejected (stock): item={request.item_id}, "
                f"requested={request.quantity}, available={stock_res.remaining}"
            )

            response.success = False
            response.status = "rejected"
            response.detail = f"stock: {stock_res.reason}"
            response.remaining_stock = stock_res.remaining
            response.payment_auth_code = ""
            return response
        
        # discount
        discount_req = DiscountApply.Request()
        discount_req.item_id = request.item_id
        discount_req.original_amount = request.amount

        discount_res = self.discount_cli.call(discount_req)
        request.amount = discount_res.discounted_amount

        # 결제 승인
        pay_req = AuthorizePayment.Request()
        pay_req.order_id = request.order_id
        pay_req.amount = request.amount
        pay_req.currency = request.currency

        pay_res = self.pay_cli.call(pay_req)

        if not pay_res.approved:
            self.get_logger().warn(
                f"Order rejected (payment): order_id={request.order_id}"
            )

            response.success = False
            response.status = "rejected"
            response.detail = f"payment: {pay_res.reason}"
            response.remaining_stock = stock_res.remaining
            response.payment_auth_code = ""
            return response

        # 성공
        response.success = True
        response.status = "success"
        if discount_res.discount_rate > 0:
            response.detail = f"order accepted (discount: {discount_res.discount_rate}%, final: {discount_res.discounted_amount} {request.currency})"
        else:
            response.detail = "order accepted"
        response.remaining_stock = stock_res.remaining
        response.payment_auth_code = pay_res.auth_code

        self.get_logger().info(
            f"Order success: remaining={response.remaining_stock}, "
            f"auth={response.payment_auth_code}"  
        )

        return response

def main():
    rclpy.init()
    node = OrderManager()

    # 멀티스레드 실행기 (동기 서비스 체인에 필수)
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()