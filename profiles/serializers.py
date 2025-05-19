from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator
from .models import *

class EmailUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value.lower()

class UserSerializer2(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'phone_number', 'password', 'status', 'role', 'birth_date',
            'gender', 'address', 'profile', 'avatar_url', 'bio'
        ]

    def create(self, validated_data):
        try:
            self.validate_phone_number(validated_data['phone_number'])
            # self.validate_role(validated_data['role'])
            # self.validate_status(validated_data['status'])
            validated_data['password'] = make_password(validated_data['password'])
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError({"error": "Failed to create user", "details": str(e)})

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

    def validate_phone_number(self, value):
        phone_validator = RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be in international format: +[country code][number]."
        )
        phone_validator(value)
        return value

    # class EmailUpdateSerializer(serializers.Serializer):
    # email = serializers.EmailField()
    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value.lower()
    
    def validate_role(self, value):
        allowed_roles = [choice[0] for choice in UserRole.choices]
        if value not in allowed_roles:
            raise serializers.ValidationError(f"Invalid role. Choose from: {', '.join(allowed_roles)}")
        return value

    def validate_status(self, value):
        allowed_statuses = [choice[0] for choice in UserStatus.choices]
        if value not in allowed_statuses:
            raise serializers.ValidationError(f"Invalid status. Choose from: {', '.join(allowed_statuses)}")
        return value

    # def validate_gender(self, value):
    #     allowed_genders = [choice[0] for choice in Gender.choices]
    #     if value not in allowed_genders:
    #         raise serializers.ValidationError(f"Invalid gender. Choose from: {', '.join(allowed_genders)}")
    #     return value
    


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = '__all__'
        fields = ['id', 'username', 'email','phone_number','avatar_url', 'first_name', 'last_name', 'role', 'status', 'birth_date' ]


        