from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .serializers import LoginSerializer, UserSerializer, RegisterSerializer


class AuthViewSet(viewsets.ViewSet):
    """
    Authentication endpoints
    """
    
    @action(detail=False, methods=['post'], authentication_classes=[], permission_classes=[])
    def login(self, request):
        """
        Login endpoint
        POST /api/auth/login/
        
        Body:
        {
            "username": "admin",
            "password": "admin123"
        }
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        login(request, user)
        
        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)
        
        # Determine role
        role = 'admin' if user.is_staff else 'employee'
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': role,
                'is_admin': user.is_staff,
                'is_superuser': user.is_superuser
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], authentication_classes=[], permission_classes=[])
    def register(self, request):
        """
        Register endpoint
        POST /api/auth/register/
        
        Body:
        {
            "username": "john",
            "email": "john@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "role": "employee"
        }
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if username already exists
        if User.objects.filter(username=serializer.validated_data['username']).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email already exists
        email = serializer.validated_data.get('email')
        if email and User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data.get('email', ''),
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', '')
        )
        
        # Set role (admin or employee)
        role = serializer.validated_data.get('role', 'employee')
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()
        
        # Create token
        token, _ = Token.objects.get_or_create(user=user)
        
        # Auto-login
        login(request, user)
        
        return Response({
            'success': True,
            'message': 'Registration successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': role,
                'is_admin': user.is_staff
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Logout endpoint
        POST /api/auth/logout/
        """
        logout(request)
        
        # Delete token if it exists
        try:
            request.user.auth_token.delete()
        except:
            pass
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user info
        GET /api/auth/me/
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = request.user
        role = 'admin' if user.is_staff else 'employee'
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': role,
            'is_admin': user.is_staff,
            'is_superuser': user.is_superuser
        }, status=status.HTTP_200_OK)
