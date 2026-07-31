from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils.cache import patch_cache_control, patch_vary_headers

from .models import User
from .serializers import ChangePasswordSerializer, MyTokenObtainPairSerializer, RegisterSerializer, UserSerializer


class PrivateNoStoreMixin:
    """Keep credentials and authenticated profile data out of browser/proxy caches."""

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        patch_cache_control(response, private=True, no_store=True)
        patch_vary_headers(response, ("Authorization",))
        return response


class MyTokenObtainPairView(PrivateNoStoreMixin, TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class RegisterView(PrivateNoStoreMixin, generics.CreateAPIView):
    queryset = User.objects.none()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class ProfileView(PrivateNoStoreMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    put = patch


class ChangePasswordView(PrivateNoStoreMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class LogoutView(PrivateNoStoreMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)
