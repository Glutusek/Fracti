from django.contrib.auth.models import User
from rest_framework import serializers

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True) # Hasło tylko do zapisu!

    class Meta:
        model = User
        # Tu wskazujemy, że chcemy zapisać email do standardowego modelu User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        # Tworzymy usera używając wbudowanej metody create_user
        # Ona automatycznie hashuje hasło i zapisuje email w dobrej kolumnie
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user