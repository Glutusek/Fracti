from django.contrib.auth.models import User
from rest_framework import serializers

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
    
    def validate_username(self, value):
        if len(value) < 3 or len(value) > 150:
            raise serializers.ValidationError("Username musi mieć 3-150 znaków")
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Username może zawierać tylko litery, cyfry, _ i -")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email już istnieje")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id', 'username')

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'username':
                continue
            setattr(instance, attr, value)
        instance.save()
        return instance