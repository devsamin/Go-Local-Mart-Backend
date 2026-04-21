# # from rest_framework import serializers
# # from .models import User


# # # ✅ Signup Serializer
# # class RegisterSerializer(serializers.ModelSerializer):
# #     password = serializers.CharField(write_only=True, min_length=6)

# #     class Meta:
# #         model = User
# #         fields = [
# #             'id', 'username', 'email', 'password', 'role',
# #             'location', 'phone', 'address', 'photo',
# #             'businessName', 'nidNumber', 'bankAccount'
# #         ]

# #     def create(self, validated_data):
# #         password = validated_data.pop('password')
# #         user = User(**validated_data)
# #         user.set_password(password)
# #         user.save()
# #         return user


# # # ✅ Profile / Read Serializer
# # class UserSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = User
# #         fields = [
# #             'id', 'username', 'email', 'role',
# #             'location', 'phone', 'address', 'photo',
# #             'businessName', 'nidNumber', 'bankAccount'
# #         ]
# #         read_only_fields = ['email', 'role']


# # # ⚙️ Optional: Custom Login Serializer (যদি token manually নিতে চাও)
# # class LoginSerializer(serializers.Serializer):
# #     # email = serializers.EmailField()
# #     username = serializers.CharField()
# #     password = serializers.CharField(write_only=True)


# from rest_framework import serializers
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from django.contrib.auth import authenticate
# from .models import User


# # ✅ Signup Serializer
# class RegisterSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, min_length=6)

#     class Meta:
#         model = User
#         fields = [
#             'id', 'username', 'email', 'password', 'role',
#             'location', 'phone', 'address', 'photo',
#             'businessName', 'nidNumber', 'bankAccount'
#         ]

#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         user = User(**validated_data)
#         user.set_password(password)
#         user.save()
#         return user


# # ✅ Profile / Read Serializer
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = [
#             'id', 'username', 'email', 'role',
#             'location', 'phone', 'address', 'photo',
#             'businessName', 'nidNumber', 'bankAccount'
#         ]
#         read_only_fields = ['email', 'role']


# # ✅ Custom JWT Login Serializer (With Role Validation)
# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     # accept role from frontend
#     role = serializers.CharField(required=False)

#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#         token['username'] = user.username
#         token['role'] = user.role
#         return token

#     def validate(self, attrs):
#         username = attrs.get("username")
#         password = attrs.get("password")
#         role = attrs.get("role")

#         # Authenticate user
#         user = authenticate(username=username, password=password)
#         if not user:
#             raise serializers.ValidationError("ইউজারনেম বা পাসওয়ার্ড সঠিক নয়!")

#         # ✅ Role check
#         if role and user.role != role:
#             raise serializers.ValidationError(
#                 f"আপনি {user.role} হিসেবে নিবন্ধিত। দয়া করে সঠিক ভূমিকা নির্বাচন করুন।"
#             )

#         # Continue JWT token generation
#         data = super().validate(attrs)
#         data['username'] = user.username
#         data['role'] = user.role
#         return data


from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import User


# Register / Signup
class RegisterSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'role',
            'location', 'phone', 'address', 'photo',
            'businessName', 'nidNumber', 'bankAccount'
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("এই ইমেইলটি ইতিমধ্যে ব্যবহৃত হয়েছে।")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# User Profile / Read
class UserSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role',
            'location', 'phone', 'address', 'photo',
            'businessName', 'nidNumber', 'bankAccount'
        ]
        read_only_fields = ['email', 'role']

    def get_photo(self, obj):
        if obj.photo:
            return obj.photo.url   # 🔥 Cloudinary URL return করবে
        return None

# JWT Login with role validation
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    role = serializers.CharField(required=False)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        return token

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        role = attrs.get("role")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("ইউজারনেম বা পাসওয়ার্ড সঠিক নয়!")

        if role and user.role != role:
            raise serializers.ValidationError(
                f"আপনি {user.role} হিসেবে নিবন্ধিত। দয়া করে সঠিক ভূমিকা নির্বাচন করুন।"
            )

        data = super().validate(attrs)
        data['username'] = user.username
        data['role'] = user.role
        return data


# from rest_framework import serializers

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("বর্তমান পাসওয়ার্ড সঠিক নয়")
        return value
