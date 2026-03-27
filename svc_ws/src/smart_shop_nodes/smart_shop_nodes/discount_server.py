import rclpy
from rclpy.node import Node

from smart_shop_interfaces.srv import DiscountApply

class DiscountServer(Node):
    def __init__(self):
        super().__init__('discount_server')
        self.srv = self.create_service(
            DiscountApply,
            'discount_apply',
            self.cb_discount_apply
        )

    def cb_discount_apply(self, request, response):
        if request.item_id == 'cup':
            response.discounted_amount = request.original_amount*0.9
            response.discount_rate = 10
            response.reason = r"10% discount"
        elif request.item_id == 'snack':
            response.discounted_amount = request.original_amount*0.8
            response.discount_rate = 20
            response.reason = r"20% discount"
        elif request.item_id == 'bottle':
            response.discounted_amount = request.original_amount
            response.discount_rate = 0
            response.reason = 'no discount'
        else:
            response.discounted_amount = request.original_amount
            response.discount_rate = 0
            response.reason = 'no discount'
        return response
        

def main():
    rclpy.init()
    node = DiscountServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
