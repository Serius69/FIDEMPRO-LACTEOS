from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Variable
from .serializers import VariableSerializer

@api_view(['GET', 'POST'])
def VariableList(request):
    if request.method == 'GET':
        variables = Variable.objects.all()
        serializer = VariableSerializer(variables, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = VariableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def VariableDetail(request, id):
    try:
        variable = Variable.objects.get(id=id)
    except Variable.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = VariableSerializer(variable)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = VariableSerializer(variable, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        variable.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
