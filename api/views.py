
from rest_framework import viewsets, status
from .models import Movie, Comment
from .serializers import MovieSerializer, CommentSerializer,UserSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = (MovieSerializer)
    authentication_classes = (TokenAuthentication, )
    #permission_classes = (IsAuthenticated,)


    @action(detail=True, methods=['POST'])
    def comment_movie(self, request, pk=None):
       
        if 'text' in request.data:

            movie = Movie.objects.get(id=pk)
            text = request.data['text']
            user =request.user
            print('\n\n\n',user, text)
            try:
                comment =Comment.objects.get(user = user.id, movie = movie.id)
                comment.text = text
                comment.save()
                serializer = CommentSerializer(comment, many=False)
                response = {'message': 'Comment update', 'resut': serializer.data}
                return Response(response, status=status.HTTP_200_OK)
            except:
                comment = Comment.objects.create(user = user, movie = movie, text = text)
                serializer = CommentSerializer(comment, many=False)
                response = {'message': 'Comment create', 'resut': serializer.data}
                return Response(response, status=status.HTTP_200_OK)
            
        else:
            response = {'message': 'you need to provide text'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = (CommentSerializer)
    """ authentication_classes = (TokenAuthentication, )
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated,)

    def update(self, *args, **kwargs):
        response = {'message': 'you cant update rating like that '}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def create(self, *args, **kwargs):
        response = {'message': 'you cant create rating like that '}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)"""

