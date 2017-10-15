from rest_framework import serializers


class DeviceSerializer(serializers.Serializer):
    device = serializers.ChoiceField(choices=('mobile', 'web',), required=False)
