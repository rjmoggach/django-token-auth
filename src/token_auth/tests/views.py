from django.http import HttpResponse

def example(request):
    return HttpResponse('reached the view')