from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import AnonRateThrottle
from rest_framework import generics
from .serializers import ContactMessageSerializer, AdminContactMessageSerializer
from .models import ContactMessage


class ContactCreateView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContactListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdminContactMessageSerializer

    def get_queryset(self):
        return ContactMessage.objects.order_by('-created_at')


class ContactDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return ContactMessage.objects.get(pk=pk)
        except ContactMessage.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = AdminContactMessageSerializer(obj)
        return Response(serializer.data)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        read_val = request.data.get('read')
        if read_val is None:
            return Response({'detail': 'Provide `read` field.'}, status=status.HTTP_400_BAD_REQUEST)
        obj.read = bool(read_val)
        obj.save()
        serializer = AdminContactMessageSerializer(obj)
        return Response(serializer.data)

