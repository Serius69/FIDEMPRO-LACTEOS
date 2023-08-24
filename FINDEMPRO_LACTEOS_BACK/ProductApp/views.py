from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse
from ProductApp.serializers import ProductSerializer
from ProductApp.models import Product

@csrf_exempt
def productApi(request,id=0):
    if request.method=='GET':
        product = Product.objects.all()
        product_serializer=ProductSerializer(product,many=True)
        return JsonResponse(product_serializer.data,safe=False)
    elif request.method=='POST':
        product_data=JSONParser().parse(request)
        product_serializer=ProductSerializer(data=product_data)
        if product_serializer.is_valid():
            product_serializer.save()
            return JsonResponse("Added Successfully",safe=False)
        return JsonResponse("Failed to Add",safe=False)
    elif request.method=='PUT':
        product_data=JSONParser().parse(request)
        product=product.objects.get(id=id)
        product_serializer=ProductSerializer(product,data=product_data)
        if product_serializer.is_valid():
            product_serializer.save()
            return JsonResponse("Updated Successfully",safe=False)
        return JsonResponse("Failed to Update")
    elif request.method=='DELETE':
        product=product.objects.get(id=id)
        product.delete()
        return JsonResponse("Deleted Successfully",safe=False)
