from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse
from VariableApp.serializers import VariableSerializer
from VariableApp.models import Variable

@csrf_exempt
def VariableApi(request,id=0):
    if request.method=='GET':
        Variable = Variable.objects.all()
        Variable_serializer=VariableSerializer(Variable,many=True)
        return JsonResponse(Variable_serializer.data,safe=False)
    elif request.method=='POST':
        Variable_data=JSONParser().parse(request)
        Variable_serializer=VariableSerializer(data=Variable_data)
        if Variable_serializer.is_valid():
            Variable_serializer.save()
            return JsonResponse("Added Successfully",safe=False)
        return JsonResponse("Failed to Add",safe=False)
    elif request.method=='PUT':
        Variable_data=JSONParser().parse(request)
        Variable=Variable.objects.get(id=id)
        Variable_serializer=VariableSerializer(Variable,data=Variable_data)
        if Variable_serializer.is_valid():
            Variable_serializer.save()
            return JsonResponse("Updated Successfully",safe=False)
        return JsonResponse("Failed to Update")
    elif request.method=='DELETE':
        Variable=Variable.objects.get(id=id)
        Variable.delete()
        return JsonResponse("Deleted Successfully",safe=False)

