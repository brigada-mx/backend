class DynamicFieldsMixin:
    """A serializer mixin that takes an additional `fields` argument that controls
    which fields are included in an object's serialized representation.
    Usage:
        class MySerializer(DynamicFieldsMixin, serializers.ModelSerializer):

    Gotcha: a serializer can't inherit from this mixin if it also inherits from a
    class that uses the mixin.

    Taken from: https://gist.github.com/dbrgn/4e6fc1fe5922598592d6
    """
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('_include_fields', None)
        super(DynamicFieldsMixin, self).__init__(*args, **kwargs)
        if self.context:
            fields_string = self.context['request'].query_params.get('fields')
            if fields_string:
                fields = fields_string.split(',')
        if not fields:
            return

        allowed = set(fields)  # drop any fields that are not specified in the `fields` argument
        existing = set(self.fields.keys())
        for field_name in existing - allowed:
            self.fields.pop(field_name)
