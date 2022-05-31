from django.contrib.auth.models import User
from rest_framework import serializers
from search.models import EuIndex


class EuIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = EuIndex
        fields =  '__all__'
