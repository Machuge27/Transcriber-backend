from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    access = serializers.SerializerMethodField()
    refresh = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'access', 'refresh')
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate(self, attrs):
        """Ensure passwords match and check if email already exists"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )

        return attrs

    def create(self, validated_data):
        """Remove password2 and create user properly"""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)

        return user  # Return the actual user object

    def get_access(self, obj):
        """Generate Access Token"""
        refresh = RefreshToken.for_user(obj)
        return str(refresh.access_token)

    def get_refresh(self, obj):
        """Generate Refresh Token"""
        refresh = RefreshToken.for_user(obj)
        return str(refresh)
