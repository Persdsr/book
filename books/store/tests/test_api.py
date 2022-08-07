import json

from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BookAPITestCase(APITestCase):
    def setUp(self):
        self.assertEqual(0, Book.objects.all().count())
        self.user = User.objects.create(username="test_username")
        self.book_1 = Book.objects.create(name='Test book 1', price=25,
                                          author_name='Author 1',
                                          owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', price=55,
                                          author_name='Author 2')
        self.book_3 = Book.objects.create(name='Test book 3 Author 1', price=55,
                                          author_name='Author 3')

        UserBookRelation.objects.create(user=self.user, book=self.book_1, like=True,
                                        rate=5)

    def test_get(self):
        url = reverse('book-list')
        response = self.client.get(url)
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate')).order_by('id')
        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[0]['rating'], '5.00')
        self.assertEqual(serializer_data[0]['annotated_likes'], 1)

    def test_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author 1'})

        books = Book.objects.filter(id__in=[self.book_1.id, self.book_3.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))).order_by('id')
        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)


    #def test_ordering(self):
    #    url = reverse('book-list')
    #    response = self.client.get(url, data={'ordering': 'price'})
#
    #    books = Book.objects.filter(id__in=[self.book_1.id]).annotate(
    #        annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))))
#
    #    serializer_data = BookSerializer(books, many=True).data
    #    self.assertEqual(status.HTTP_200_OK, response.status_code)
    #    self.assertEqual(serializer_data, response.data)

    def test_create(self):
        url = reverse('book-list')
        data = {
            "name": "Programming in Python 3",
            "price": 150,
            "author_name": "Mark Summerfield"
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.post(url, data=json_data,
                                    content_type='application/json')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(4, Book.objects.all().count())
        self.assertEqual(self.user, Book.objects.last().owner)

    def test_update(self):
        url = reverse('book-detail', args={self.book_1.id})
        data = {
            'name': self.book_1.name,
            'price': 1000,
            'author_name': self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_1.refresh_from_db()
        self.assertEqual(1000, self.book_1.price)

    #def test_delete(self):
    #    url = reverse('book-detail', args={self.book_1.id})
    #    self.client.force_login(self.user)
    #    response = self.client.delete(url)
    #    self.assertEqual(status.HTTP_200_OK, response.status_code)
    #    self.assertEqual()

    def test_update_not_owner(self):
        self.user2 = User.objects.create(username="test_username2")
        url = reverse('book-detail', args={self.book_1.id})
        data = {
            'name': self.book_1.name,
            'price': 1000,
            'author_name': self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        self.assertEqual({'detail': ErrorDetail(string='You do not have permission to perform this action.', code='permission_denied')}
,response.data)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.book_1.refresh_from_db()
        self.assertEqual(25, self.book_1.price)

    def test_update_not_owner_but_staff(self):
        self.user2 = User.objects.create(username="test_username2",
                                         is_staff=True)
        url = reverse('book-detail', args={self.book_1.id})
        data = {
            'name': self.book_1.name,
            'price': 1000,
            'author_name': self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_1.refresh_from_db()
        self.assertEqual(1000, self.book_1.price)


class BookRelationTestCase(APITestCase):
    def setUp(self):
        self.assertEqual(0, Book.objects.all().count())
        self.user = User.objects.create(username="test_username")
        self.user2 = User.objects.create(username="test_username2")
        self.book_1 = Book.objects.create(name='Test book 1', price=25,
                                          author_name='Author 1',
                                          owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', price=55,
                                          author_name='Author 2')

    def test_like(self):
        url = reverse('userbookrelation-detail', args={self.book_1.id})

        data = {
            'like': True,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                   content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertTrue(relation.like)

    def test_rate(self):
        url = reverse('userbookrelation-detail', args={self.book_1.id})

        data = {
            'rate': 3,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertEqual(3, relation.rate)

    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args={self.book_1.id})

        data = {
            'rate': 6,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)


