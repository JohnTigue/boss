from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from django.db import IntegrityError, transaction

from .serializers import *
from .lookup import LookUpKey
from .error import BossError, BossHTTPError

from . import metadb
from .request import BossRequest


class CollectionObj(APIView):
    """
    View to access a collection object

    """
    def get(self, request, collection):
        """
        View to handle GET requests for a Collection

        :param request: DRF Request object
        :param collection: Collection Name specifying the collection you want to get the meta data for
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
        except Collection.DoesNotExist:
            return HttpResponseBadRequest("[ERROR]- Collection  with name {} not found".format(collection))

        serializer = CollectionSerializer(collection_obj)
        return Response(serializer.data)

    def post(self, request, collection):
        """
        Post a new collection using django rest framework

        :param request: DRF Request object
        :param collection: Collection name
        :return:
        """
        serializer = CollectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, collection):
        """
        Delete a collection
        :param request: DRF Request object
        :param collection:  Name of collection to delete
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
        except Collection.DoesNotExist:
            return HttpResponseBadRequest("[ERROR]- Collection  with name {} not found".format(collection))
        collection_obj.delete()
        return HttpResponse(status=204)


class ExperimentObj(APIView):
    """
    View to access an experiment object

    """

    def get(self, request, collection, experiment):
        """
        Retrieve information about a experiment.
        :param request: DRF Request object
        :param collection: Collection name
        :param experiment: Experiment name
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
        except (Collection.DoesNotExist, Experiment.DoesNotExist):
            return HttpResponse(status=404)

        serializer = ExperimentSerializer(experiment_obj)
        return Response(serializer.data)

    def post(self, request, collection, experiment):
        """
        Post  a new experiment
        :param request: DRF Request object
        :param collection: Collection name
        :param experiment: Experiment name
        :return:
        """
        serializer = ExperimentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, collection, experiment):
        """
        Delete an experiment object given the collection and experiment name
        :param request: DRF Request object
        :param collection: Collection Name
        :param experiment: Experiment Name
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
        except (Collection.DoesNotExist, Experiment.DoesNotExist):
            return HttpResponse(status=404)

        experiment_obj.delete()
        return HttpResponse(status=204)


class ChannelLayerObj(APIView):
    """
    View to access a channel

    """

    def get(self, request, collection, experiment, channel_layer):
        """
        Retrieve information about a channel.
        :param request: DRF Request object
        :param collection: Collection name
        :param experiment: Experiment name
        :param channel_layer: Channel or Layer name
        :return:
        """

        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_layer_obj = ChannelLayer.objects.get(name=channel_layer, experiment=experiment_obj)

        except (Collection.DoesNotExist, Experiment.DoesNotExist, ChannelLayer.DoesNotExist):
            return HttpResponse(status=404)

        if request.method == 'GET':
            serializer = ChannelLayerSerializer(channel_layer_obj)
            return Response(serializer.data)
        return HttpResponse(status=404)

    def post(self, request, collection, experiment, channel_layer):
        """
        Post a new Channel
        :param request: DRF Request object
        :param collection: Collection
        :param experiment: Experiment
        :param channel_layer: Channel or Layer
        :return:
        """
        serializer = ChannelLayerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, collection, experiment, channel_layer):
        """
        Delete a Channel
        :param request: DRF Request object
        :param collection: Collection
        :param experiment: Experiment
        :param channel_layer: Channel or Layer
        :return:
        """
        try:
            collection_obj = Collection.objects.get(name=collection)
            experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
            channel_layer_obj = ChannelLayer.objects.get(name=channel_layer, experiment=experiment_obj)
        except (Collection.DoesNotExist, Experiment.DoesNotExist):
            return HttpResponse(status=404)

        channel_layer_obj.delete()
        return HttpResponse(status=204)


class CollectionList(generics.ListCreateAPIView):
    """
    List all collections or create a new collection

    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new collection

        Create a new collection and an associated bosskey for that collection
        Args:
            request:
            *args:
            **kwargs:

        Returns:

        """
        col_data = request.data
        serializer = CollectionSerializer(data=col_data)

        if serializer.is_valid():
            serializer.save()

            collection = Collection.objects.get(name=col_data['name'])
            lookup_key = collection.pk
            boss_key = collection.name
            LookUpKey.add_lookup(lookup_key,boss_key,collection.name)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExperimentList(generics.ListCreateAPIView):
    """
    List all experiments
    """
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        exp_data = request.data
        serializer = ExperimentSerializer(data=exp_data)

        if serializer.is_valid():
            serializer.save()

            # Create the boss lookup entry
            experiment = Experiment.objects.get(name=exp_data['name'])
            collection = experiment.collection
            boss_key = collection.name + '&' + experiment.name
            lookup_key = str(collection.pk) + '&' + str(experiment.pk)
            LookUpKey.add_lookup(lookup_key,boss_key,collection.name,experiment.name)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ChannelList(generics.ListCreateAPIView):
    """
    List all channels
    """
    queryset = ChannelLayer.objects.filter(is_channel=True)
    serializer_class = ChannelSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        channel_data = request.data
        serializer = ChannelSerializer(data=channel_data)

        if serializer.is_valid():
            serializer.save()

            # Create the boss lookup entry
            channel = ChannelLayer.objects.get(name=channel_data['name'])
            experiment = channel.experiment
            collection = experiment.collection
            max_time_sample = experiment.max_time_sample
            boss_key = collection.name + '&' + experiment.name + '&' + channel.name
            lookup_key = str(experiment.collection.pk) + '&' + str(experiment.pk) + '&' + str(channel.pk)
            LookUpKey.add_lookup(lookup_key,boss_key,collection.name,experiment.name, channel.name, max_time_sample)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LayerList(generics.ListCreateAPIView):
    """
    List all layers
    """
    queryset = ChannelLayer.objects.filter(is_channel=False)
    serializer_class = LayerSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        layer_data = request.data
        serializer = LayerSerializer(data=layer_data)

        if serializer.is_valid():
            serializer.save()

            # Create the boss lookup entry
            layer = ChannelLayer.objects.get(name=layer_data['name'])
            experiment = layer.experiment
            collection = experiment.collection
            max_time_sample = experiment.max_time_sample
            boss_key = collection.name + '&' + experiment.name + '&' + layer.name
            lookup_key = str(experiment.collection.pk) + '&' + str(experiment.pk) + '&' + str(layer.pk)
            LookUpKey.add_lookup(lookup_key,boss_key,collection.name,experiment.name,layer.name, max_time_sample)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CoordinateFrameList(generics.ListCreateAPIView):
    """
    List all coordinate frames
    """
    queryset = CoordinateFrame.objects.all()
    serializer_class = CoordinateFrameSerializer


class BossMeta(APIView):
    """
    View to handle read,write,update and delete metadata queries
    
    """

    def get(self, request, collection, experiment=None, channel_layer=None):
        """
        View to handle GET requests for metadata

        Args:
            request: DRF Request object
            collection: Collection Name
            experiment: Experiment name. default = None
            channel_layer: Channel or Layer name

        Returns:

        """
        try:
            # Validate the request and get the lookup Key
            req = BossRequest(request)
            lookup_key = req.get_lookup_key()

        except BossError as err:
            return err.to_http()

        if not lookup_key or lookup_key[0] == "":
            return BossHTTPError(404, "Invalid request. Unable to parse the datamodel arguments", 30000)

        if 'key' not in request.query_params:
            # List all keys that are valid for the query
            mdb = metadb.MetaDB()
            mdata = mdb.get_meta_list(lookup_key[0])
            if not mdata:
                return BossHTTPError(404, "Cannot find keys that match this request", 30000)
            else:
                keys =[]
                for meta in mdata:
                    keys.append(meta['key'])
                data = {'keys': keys}
                return Response(data)

            #return BossHTTPError(404, "Missing optional argument key in the request", 30000)
        else:

            mkey = request.query_params['key']
            mdb = metadb.MetaDB()
            mdata = mdb.get_meta(lookup_key[0],mkey)
            if mdata:
                data = {'key': mdata['key'], 'value': mdata['metavalue']}
                return Response(data)
            else:
                return BossHTTPError(404, "Invalid request. Key {} Not found in the database".format(mkey), 30000)

    def post(self, request, collection, experiment= None, channel_layer=None):
        """
        View to handle POST requests for metadata

        Args:
            request: DRF Request object
            collection: Collection Name specifying the collection you want to get the meta data for
            experiment: Experiment name. default = None
            channel_layer: Channel or Layer name. Default = None

        Returns:

        """

        if 'key' not in request.query_params or 'value' not in request.query_params:
            return BossHTTPError(404, "Missing optional argument key/value in the request", 30000)

        try:
            req = BossRequest(request)
            lookup_key = req.get_lookup_key()
        except BossError as err:
            return err.to_http()

        if not lookup_key or not lookup_key[0]:
            return BossHTTPError(404, "Invalid request. Unable to parse the datamodel arguments", 30000)

        mkey = request.query_params['key']
        value = request.query_params['value']

        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB()
        if mdb.get_meta(lookup_key[0],mkey):
            return BossHTTPError(404, "Invalid request. The key {} already exists".format(mkey), 30000)
        mdb.write_meta(lookup_key[0], mkey, value)
        return HttpResponse(status=201)

    def delete(self, request, collection, experiment = None, channel_layer= None):
        """
        View to handle the delete requests for metadata
        Args:
            request: DRF Request object
            collection: Collection name. Default = None
            experiment: Experiment name. Default = None
            channel_layer: Channel_layer name . Default = None

        Returns:

        """

        if 'key' not in request.query_params:
            return BossHTTPError(404, "Missing optional argument key in the request", 30000)

        try:
            req = BossRequest(request)
            lookup_key = req.get_lookup_key()
        except BossError as err:
            return err.to_http()

        if not lookup_key:
            return BossHTTPError(404, "Invalid request. Unable to parse the datamodel arguments", 30000)



        mkey = request.query_params['key']

        # Delete metadata from the dynamodb database
        mdb = metadb.MetaDB()
        response = mdb.delete_meta(lookup_key[0],mkey)

        if 'Attributes' in response:
            return HttpResponse(status=201)
        else:
            return HttpResponseBadRequest("[ERROR]- Key {} not found ".format(mkey))

    def put(self, request, collection, experiment=None, channel_layer = None):
        """
        View to handle update requests for metadata
        Args:
            request: DRF Request object
            collection: Collection Name. Default = None
            experiment: Experiment Name. Default = None
            channel_layer: Channel Name Default + None

        Returns:

        """
        # The metadata consist of two parts. The bosskey#key
        # bosskey represents the datamodel object
        # key is the key for the meta data associated with the data model object

        if 'key' not in request.query_params or 'value' not in request.query_params:
            return BossHTTPError(404, "Missing optional argument key/value in the request", 30000)

        try:
            req = BossRequest(request)
            lookup_key = req.get_lookup_key()
        except BossError as err:
            return err.to_http()

        if not lookup_key:
            return BossHTTPError(404, "Invalid request. Unable to parse the datamodel arguments", 30000)

        mkey = request.query_params['key']
        value = request.query_params['value']

        # Post Metadata the dynamodb database
        mdb = metadb.MetaDB()
        mdb.update_meta(lookup_key[0], mkey, value)
        return HttpResponse(status=201)
