from django.http import HttpResponse
from django.views.generic import View
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

from .forms import UserForm, RoleForm, GroupForm, GroupMemberForm
from .forms import CollectionForm, ExperimentForm, ChannelForm
from .forms import CoordinateFrameForm, MetaForm

from . import api

# import as to deconflict with our Token class
from rest_framework.authtoken.models import Token as TokenModel

class Home(LoginRequiredMixin, View):
    def get(self, request):
        return HttpResponse(render_to_string('base.html'))

class Users(LoginRequiredMixin, View):
    def get(self, request, user_form=None):
        delete = request.GET.get('delete')
        if delete:
            err = api.del_user(request, delete)
            if err:
                return err
            return redirect('mgmt:users')

        users, err = api.get_users(request) # search query parameter will be automatically passed
        if err:
            return err

        args = {
            'users': users,
            'user_form': user_form if user_form else UserForm(),
            'user_error': "error" if user_form else "",
        }
        return HttpResponse(render_to_string('users.html', args, RequestContext(request)))

    def post(self, request):
        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            username = data['username']
            del data['username']
            del data['verify_password']

            err = api.add_user(request, username, data)
            if err:
                return err
            return redirect('mgmt:users')
        else:
            return self.get(request, user_form=form)

class User(LoginRequiredMixin, View):
    def get(self, request, username, role_form=None):
        # DP NOTE: Using BossUserRole because BossUser doesn't add anything
        #          that is useful to display
        remove = request.GET.get('remove')
        if remove is not None:
            err = api.del_role(request, username, remove)
            if err:
                return err
            return redirect('mgmt:user', username)

        roles, err = api.get_roles(request, username)
        if err:
            return err

        args = {
            'username': username,
            'roles': roles,
            'role_form': role_form if role_form else RoleForm(),
            'role_error': "error" if role_form else "",
        }
        return HttpResponse(render_to_string('user.html', args, RequestContext(request)))

    def post(self, request, username):
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']

            err = api.add_role(request, username, role)
            if err:
                return err
            return redirect('mgmt:user', username)
        else:
            return self.get(request, username, role_form=form)

class Token(LoginRequiredMixin, View):
    def get(self, request):
        try:
            token = TokenModel.objects.get(user = request.user)
            button = "Revoke Token"
        except:
            token = None
            button = "Generate Token"

        args = {
            'username': request.user,
            'token': token,
            'button': button,
        }
        return HttpResponse(render_to_string('token.html', args, RequestContext(request)))

    def post(self, request):
        try:
            token = TokenModel.objects.get(user = request.user)
            token.delete()
        except:
            token = TokenModel.objects.create(user = request.user)

        return redirect('mgmt:token')

class Groups(LoginRequiredMixin, View):
    def get(self, request, group_form=None):
        delete = request.GET.get('delete')
        if delete:
            err = api.del_group(request, delete)
            if err:
                return err
            return redirect('mgmt:groups')

        # can only modify groups the user is a maintainer of
        groups, err = api.get_groups(request, maintainer_only=True)
        if err:
            return err

        args = {
            'groups': groups,
            'group_form': group_form if group_form else GroupForm(),
            'group_error': "error" if group_form else ""
        }
        return HttpResponse(render_to_string('groups.html', args, RequestContext(request)))

    def post(self, request):
        form = GroupForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']

            err = api.add_group(request, group_name)
            if err:
                return err
            return redirect('mgmt:groups')
        else:
            return self.get(request, group_form=form)

class Group(LoginRequiredMixin, View):
    def get(self, request, group_name, perm_form=None):
        remove = request.GET.get('rem_memb')
        if remove is not None:
            err = api.del_member(request, group_name, remove)
            if err:
                return err
            return redirect('mgmt:group', group_name)

        remove = request.GET.get('rem_maint')
        if remove is not None:
            err = api.del_maintainer(request, group_name, remove)
            if err:
                return err
            return redirect('mgmt:group', group_name)

        members, err = api.get_members(request, group_name)
        if err:
            return err

        maintainers, err = api.get_maintainers(request, group_name)
        if err:
            return err

        data = {}
        for member in members:
            data[member] = 'member'
            if member in maintainers:
                data[member] += '+maintainer'
        for maintainer in maintainers:
            if maintainer not in members:
                data[maintainer] = 'maintainer'


        args = {
            'group_name': group_name,
            'rows': data.items(),
            'members': members,
            'maintainers': maintainers,
            'perm_form': perm_form if perm_form else GroupMemberForm(),
            'perm_error': "error" if perm_form else "",
        }
        return HttpResponse(render_to_string('group.html', args, RequestContext(request)))

    def post(self, request, group_name):
        form = GroupMemberForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            role = form.cleaned_data['role']

            if 'member' in role:
                err = api.add_member(request, group_name, user)
                if err:
                    return err

            if 'maintainer' in role:
                err = api.add_maintainer(request, group_name, user)
                if err:
                    return err

            return redirect('mgmt:group', group_name)
        else:
            return self.get(request, group_name, perm_form=form)

class Resources(LoginRequiredMixin, View):
    def get(self, request, col_form=None, coord_form=None):
        delete = request.GET.get('del_col')
        if delete:
            err = api.del_collection(request, delete)
            if err:
                return err
            return redirect('mgmt:resources')

        delete = request.GET.get('del_coord')
        if delete:
            err = api.del_coord(request, delete)
            if err:
                return err
            return redirect('mgmt:resources')

        collections, err = api.get_collections(request)
        if err:
            return err

        coords, err = api.get_coords(request)
        if err:
            return err

        args = {
            'collections': collections,
            'coords': coords,
            'col_form': col_form if col_form else CollectionForm(),
            'col_error': "error" if col_form else "",
            'coord_form': coord_form if coord_form else CoordinateFrameForm(),
            'coord_error': "error" if coord_form else "",
        }
        return HttpResponse(render_to_string('collections.html', args, RequestContext(request)))

    def post(self, request):
        action = request.GET.get('action') # URL parameter

        if action == 'col':
            form = CollectionForm(request.POST)
            if form.is_valid():
                collection = form.cleaned_data['collection']
                description = form.cleaned_data['description']
                data = {'description': description}

                err = api.add_collection(request, collection, data)
                if err:
                    return err
                return redirect('mgmt:resources')
            else:
                return self.get(request, col_form=form)
        elif action == 'coord':
            form = CoordinateFrameForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                coord_name = data['name']

                err = api.add_coord(request, coord_name, data)
                if err:
                    return err
                return redirect('mgmt:resources')
            else:
                return self.get(request, coord_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")

class CoordinateFrame(LoginRequiredMixin, View):
    def get(self, request, coord_name, coord_form=None):
        coord, err = api.get_coord(request, coord_name)
        if err:
            return err

        args = {
            'coord_name': coord_name,
            'coord_form': coord_form if coord_form else CoordinateFrameForm(coord),
            'coord_error': "error" if coord_form else "",
        }
        return HttpResponse(render_to_string('coordinate_frame.html', args, RequestContext(request)))

    def post(self, request, coord_name):
            form = CoordinateFrameForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                # Cannot send readonly properties in the request
                # If they were modified, it will be discarded
                ro = ['z_start',
                      'voxel_unit',
                      'y_voxel_size',
                      'time_step_unit',
                      'y_start',
                      'x_start',
                      'time_step',
                      'x_stop',
                      'x_voxel_size',
                      'y_stop',
                      'z_stop',
                      'z_voxel_size']
                for key in ro:
                    del data[key]

                err = api.up_coord(request, coord_name, data)
                if err:
                    return err
                return redirect('mgmt:coord', coord_name)
            else:
                return self.get(request, coord_name, coord_form=form)

class Collection(LoginRequiredMixin, View):
    def get(self, request, collection_name, exp_form=None, meta_form=None):
        remove = request.GET.get('rem_exp')
        if remove is not None:
            err = api.del_experiment(request, collection_name, remove)
            if err:
                return err
            return redirect('mgmt:collection', collection_name)

        remove = request.GET.get('rem_meta')
        if remove is not None:
            err = api.del_meta(request, remove, collection_name)
            if err:
                return err
            return redirect('mgmt:collection', collection_name)

        collection, err = api.get_collection(request, collection_name)
        if err:
            return err

        metas, err = api.get_meta_keys(request, collection_name)
        if err:
            return err

        args = {
            'collection_name': collection_name,
            'collection': collection,
            'metas': metas,
            'exp_form': exp_form if exp_form else ExperimentForm(),
            'exp_error': "error" if exp_form else "",
            'meta_form': meta_form if meta_form else MetaForm(),
            'meta_error': "error" if meta_form else "",
        }
        return HttpResponse(render_to_string('collection.html', args, RequestContext(request)))

    def post(self, request, collection_name):
        action = request.GET.get('action') # URL parameter

        if action == 'exp':
            form = ExperimentForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                experiment_name = data['name']

                err = api.add_experiment(request, collection_name, experiment_name, data)
                if err:
                    return err
                return redirect('mgmt:collection', collection_name)
            else:
                return self.get(request, collection_name, exp_form=form)
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name)
                if err:
                    return err
                return redirect('mgmt:collection', collection_name)
            else:
                return self.get(request, collection_name, meta_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")

class Experiment(LoginRequiredMixin, View):
    def get(self, request, collection_name, experiment_name, chan_form=None, meta_form=None):
        remove = request.GET.get('rem_chan')
        if remove is not None:
            err = api.del_channel(request, collection_name, experiment_name, remove)
            if err:
                return err
            return redirect('mgmt:experiment', collection_name, experiment_name)

        remove = request.GET.get('rem_meta')
        if remove is not None:
            err = api.del_meta(request, remove, collection_name, experiment_name)
            if err:
                return err
            return redirect('mgmt:experiment', collection_name, experiment_name)

        experiment, err = api.get_experiment(request, collection_name, experiment_name)
        if err:
            return err

        channels, err = api.get_channels(request, collection_name, experiment_name)
        if err:
            return err

        metas, err = api.get_meta_keys(request, collection_name, experiment_name)
        if err:
            return err

        args = {
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'exp_form': ExperimentForm(experiment),
            'channels': channels,
            'metas': metas,
            'chan_form': chan_form if chan_form else ChannelForm(),
            'chan_error': "error" if chan_form else "",
            'meta_form': meta_form if meta_form else MetaForm(),
            'meta_error': "error" if meta_form else "",
        }
        return HttpResponse(render_to_string('experiment.html', args, RequestContext(request)))

    def post(self, request, collection_name, experiment_name):
        action = request.GET.get('action') # URL parameter

        if action == 'chan':
            form = ChannelForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                channel_name = data['name']
                if 'source' not in data or len(data['source']) == 0:
                    data['source'] = []
                else:
                    data['source'] = data['source'].split(',')
                if 'related' not in data or len(data['related']) == 0:
                    data['related'] = []
                else:
                    data['related'] = data['related'].split(',')

                err = api.add_channel(request, collection_name, experiment_name, channel_name, data)
                if err:
                    return err
                return redirect('mgmt:experiment', collection_name, experiment_name)
            else:
                return self.get(request, collection_name, experiment_name, exp_form=form)
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name, experiment_name)
                if err:
                    return err
                return redirect('mgmt:experiment', collection_name, experiment_name)
            else:
                return self.get(request, collection_name, experiment_name, meta_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")

class Channel(LoginRequiredMixin, View):
    def get(self, request, collection_name, experiment_name, channel_name, meta_form=None):
        remove = request.GET.get('rem_meta')
        if remove is not None:
            err = api.del_meta(request, remove, collection_name, experiment_name, channel_name)
            if err:
                return err
            return redirect('mgmt:channel', collection_name, experiment_name, channel_name)

        channel, err = api.get_channel(request, collection_name, experiment_name, channel_name)
        if err:
            return err

        metas, err = api.get_meta_keys(request, collection_name, experiment_name, channel_name)
        if err:
            return err

        args = {
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'channel_name': channel_name,
            'form': ChannelForm(channel),
            'metas': metas,
            'meta_form': meta_form if meta_form else MetaForm(),
            'meta_error': "error" if meta_form else "",
        }
        return HttpResponse(render_to_string('channel.html', args, RequestContext(request)))

    def post(self, request, collection_name, experiment_name, channel_name):
        action = request.GET.get('action') # URL parameter

        if action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name, experiment_name, channel_name)
                if err:
                    return err
                return redirect('mgmt:channel', collection_name, experiment_name, channel_name)
            else:
                return self.get(request, collection_name, experiment_name, channel_name, meta_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")

class Meta(LoginRequiredMixin, View):
    def get(self, request, collection, experiment=None, channel=None):
        key = request.GET['key']
        meta, err = api.get_meta(request, key, collection, experiment, channel)
        if err:
            return err

        if channel is not None:
            category = "Channel"
            category_name = channel
        elif experiment is not None:
            category = "Experiment"
            category_name = experiment
        else:
            category = "Collection"
            category_name = collection

        args = {
            'category': category,
            'category_name': category_name,
            'key': meta['key'],
            'value': meta['value'],
        }
        return HttpResponse(render_to_string('meta.html', args, RequestContext(request)))
