from drf_yasg.inspectors import SwaggerAutoSchema


class CustomAutoSchema(SwaggerAutoSchema):
    def get_operation_id(self, operation_keys):
        if len(operation_keys) > 0 and operation_keys[0] == 'api':
            return super().get_operation_id(operation_keys[1:])
        return super().get_operation_id(operation_keys)

    def get_tags(self, operation_keys):
        if len(operation_keys) > 1 and operation_keys[0] == 'api':
            return [operation_keys[1].upper()]
        return [operation_keys[0].upper()]
