# from rest_framework import generics, permissions
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework_simplejwt.views import TokenObtainPairView
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from .models import User
# from .serializers import RegisterSerializer, UserSerializer

# # ✅ Custom JWT Token Serializer (extra user info include)
# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#         token['username'] = user.username
#         token['role'] = user.role
#         return token

# # ✅ JWT Login View
# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = MyTokenObtainPairSerializer


# # ✅ Register / Signup View
# class RegisterView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = RegisterSerializer
#     permission_classes = [permissions.AllowAny]



# # ✅ Profile View / Update
# class ProfileView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request):
#         serializer = UserSerializer(request.user)
#         return Response(serializer.data)

#     def put(self, request):
#         serializer = UserSerializer(request.user, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import ChangePasswordSerializer
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import RegisterSerializer, UserSerializer, MyTokenObtainPairSerializer
from rest_framework.parsers import MultiPartParser, FormParser


# ✅ JWT Login View (With Role Validation)
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# ✅ Register / Signup View
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    parser_classes = [MultiPartParser, FormParser]


# ✅ Profile View / Update
# class ProfileView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request):
#         serializer = UserSerializer(request.user)
#         return Response(serializer.data)
from rest_framework.parsers import MultiPartParser, FormParser

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # 🔥 important

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return Response(
                {"message": "পাসওয়ার্ড সফলভাবে পরিবর্তন হয়েছে"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
