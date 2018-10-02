from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.decorators.http import condition
from django.views.generic.base import View
from sitecats.utils import get_category_model
from xross.toolbox import xross_view, xross_listener

from .models import ModelWithCompiledText
from ..integration.partners import get_partner_links
from ..exceptions import RedirectRequired, PythonzException
from ..models import ModelWithDiscussions, ModelWithCategory, User, Discussion, Article, Community, Event, Reference
from ..utils import message_info, message_warning, message_success, message_error


class RealmView(View):
    """Базовое представление для представлений областей (сущностей)."""

    realm = None  # Во время исполнения будет содержать ссылку на объект области Realm
    name = None  # Во время исполнения будет содержать алиас этого представления (н.п. edit).

    func_etag = None
    """Может указывать на метод, реализующий возвращение ETag."""
    func_last_mod = None
    """Может указывать на метод, возвращающий дату Last-Modified."""

    def dispatch(self, request, *args, **kwargs):

        @condition(self.func_etag, self.func_last_mod)
        def conditional_dispatch(request, *args, **kwargs):
            return super(RealmView, self).dispatch(request, *args, **kwargs)

        if request.method.lower() == 'get':
            # Кеширование GET-выдач.
            return conditional_dispatch(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def check_view_permissions(self, request, item):
        """Производит провердку возможности доступа к просмотру страницы.
        Возбуждает исключения, в случае ошибкидоступа.

        :param Request request:
        :param Model item:
        :return:
        """
        if not request.user.is_superuser:
            if item.is_deleted:
                # Запрещаем доступ к удалённым.
                raise Http404()

            elif item.is_draft and hasattr(item, 'submitter') and item.submitter != request.user:
                # Закрываем доступ к чужим черновикам.
                raise PermissionDenied()

    def check_edit_permissions(self, request, item):
        """Производит проверку прав пользователя для доступа к редактированию объекта.

        :param Request request:
        :param Model item:
        :return:
        """
        if not self.realm.is_allowed_edit():  # Область не поддерживает редактирования.
            raise PermissionDenied()

        if not request.user.is_authenticated:  # Неавторизованные пользователи не могут ничего.
            raise PermissionDenied()

        if not request.user.is_superuser:

            try:
                edit_by_owner = (request.user.id == item.submitter_id)
            except AttributeError:
                edit_by_owner = (request.user == item)  # Модель User

            if not edit_by_owner:
                personal_edit_models = User, Article, Discussion
                if self.realm.model in personal_edit_models:
                    raise PermissionDenied()

                # Запрещаем редактирование опубликованных материалов.
                public_edit_models = Community, Event, Reference
                if item.is_published and self.realm.model not in public_edit_models:
                    message_warning(
                        request, 'Этот материал уже прошёл модерацию и был опубликован. '
                                 'На данный момент в проекте запрещено редактирование опубликованных материалов.')
                    raise PermissionDenied()

    @classmethod
    def get_template_path(cls, name=None):
        """Возвращает путь к шаблону страницы.

        :return:
        """
        if name is None:
            name = cls.name
        return 'realms/%s/%s.html' % (cls.realm.name_plural, name)

    def render(self, request, data_dict):
        """Компилирует страницу представления.

        :param request:
        :param data_dict:
        :return:
        """
        data_dict.update({
            'realm': self.realm,
            'view': self
        })
        return render(request, self.get_template_path(), data_dict)

    def post(self, request, *args, **kwargs):
        """Запросы POST перенаправляются на обработчик GET.

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return self.get(request, *args, **kwargs)

    def update_context(self, context, request):
        """Используется для дополнения контекста шаблона данными.

        :param dict context:
        :param Request request:
        :return:
        """

    def get_object_or_404(self, obj_id):
        """Реализует механизм обнаружения объекта нужного типа для области,
        к которой привязано это представление.

        :param obj_id:
        :return:
        """
        model = self.realm.model

        q = model.objects

        related = getattr(model, 'details_related', None)
        if related:
            q = q.select_related(*related)

        if 'named/' in self.request.path:
            return get_object_or_404(q, slug=obj_id)
        else:
            return get_object_or_404(q, pk=obj_id)


class ListingView(RealmView):
    """Список объектов."""

    def get_last_modified(self, *args, **kwargs):
        """Возвращает Last-Modified для списка сущностей."""
        field = 'time_published'
        objects = self.get_paginator_objects()

        if isinstance(objects, list):
            # Если пришёл список, значит кеширование должно
            # было быть реализовано при его составлении.
            return

        last = objects.values(field).order_by(field).last()
        return last and last[field]

    func_last_mod = get_last_modified

    def get_paginator_objects(self):
        """Возвращает объекты для страницы при постраницчной навигации.

        :return:
        """
        return self.realm.model.get_paginator_objects()

    def get_most_voted_objects(self):
        """Возвращает объекты, за которые было отдано больше всего голосов.

        :return:
        """
        return self.realm.model.get_most_voted_objects()

    @classmethod
    def extend_paginator(cls, page_items):
        """Дополняет объект постраничной навигации.

        :param page_items:
        :return:
        """
        max_pages_before_after = 10
        page = page_items.number

        min_page_before = page-max_pages_before_after
        if min_page_before < 1:
            min_page_before = 0

        max_page_after = page+max_pages_before_after
        if max_page_after > page_items.paginator.num_pages:
            max_page_after = page_items.paginator.num_pages

        page_items.before_current = reversed(range(page-1, min_page_before, -1))
        page_items.after_current = range(page+1, max_page_after+1)

    def get(self, request, category_id=None):
        try:
            page = int(request.GET.get('p'))
        except (TypeError, ValueError):
            page = 1

        paginator = Paginator(self.get_paginator_objects(), self.realm.model.items_per_page)

        try:
            page_items = paginator.page(page)
        except EmptyPage:
            page_items = paginator.page(1)

        self.extend_paginator(page_items)

        category = None
        if category_id is not None:
            category = get_category_model().objects.get(pk=category_id)

        context = {
            self.realm.name_plural: page_items,
            'items': page_items,
            'category': category,
            'items_most_voted': self.get_most_voted_objects()
        }
        self.update_context(context, request)

        return self.render(request, context)

    @cached_property
    def template_list_items(self):
        return self.get_template_path('list_items')


class DetailsView(RealmView):
    """Детальная информация об объекте."""

    def _attach_support_data(self, item, request):
        """Цепляет к объекту данные о поданном за него голосе пользователя.

        :param item:
        :param request:
        :return:
        """
        item.my_support = item.is_supported_by(request.user)

    def _attach_bookmark_data(self, item, request):
        """Цепляет к объекту данные о его занесении его пользователем в избранное.

        :param item:
        :param request:
        :return:
        """
        item.is_bookmarked = item.is_bookmarked_by(request.user)

    def _attach_data(self, item, request):
        """Цепляет базовый набор данный к объекту.

        :param item:
        :param request:
        :return:
        """
        self._attach_bookmark_data(item, request)
        self._attach_support_data(item, request)

    def toggle_bookmark(self, request, action, xross=None):
        """Используется xross. Реализует занесение/изъятие объекта в/из избранного..

        :param request:
        :param action:
        :param xross:
        :return:
        """
        item = xross.attrs['item']
        if action == 1:
            item.set_bookmark(self.request.user)
        elif action == 0:
            item.remove_bookmark(self.request.user)
        self._attach_bookmark_data(item, self.request)
        return render(self.request, 'sub_box_bookmark.html', {'item': item})

    def set_rate(self, request, action, xross=None):
        """Используется xross. Реализует оценку самого объекта.

        :param request:
        :param action:
        :param xross:
        :return:
        """
        item = xross.attrs['item']
        if self._is_rating_allowed(request, item):
            if action == 1:
                item.set_support(self.request.user)
            elif action == 0:
                item.remove_support(self.request.user)
        self._attach_support_data(item, self.request)
        return render(self.request, 'sub_box_rating.html', {'item': item})

    @classmethod
    def _is_rating_allowed(cls, request, item):
        """Возвращает флаг, указывающий на то, можно
        ли рекомендовать данную сущность (материал).

        :param request:
        :param item:
        :return:
        """
        return request.user != item  # Пользователи не могут рекомендовать себя %)

    def list_partner_links(self, request, xross=None):
        """Используется xross. Реализует получение блока с партнёрскими ссылками.

        :param request:
        :param action:
        :param xross:
        :return:
        """
        item = xross.attrs['item']
        return render(request, self.get_template_path('partner_links'), get_partner_links(self.realm, item))

    @xross_view(set_rate, toggle_bookmark, list_partner_links)
    def get(self, request, obj_id):

        item = self.get_object_or_404(obj_id)

        self.check_view_permissions(request, item)

        item.has_discussions = False

        if isinstance(item, ModelWithDiscussions):
            item.has_discussions = True

        xross_listener(item=item)

        try:
            self._attach_data(item, request)
        except RedirectRequired:
            return redirect(item, permanent=True)

        item_rating_allowed = self._is_rating_allowed(request, item)

        try:
            self.check_edit_permissions(request, item)
            item_edit_allowed = True
        except PermissionDenied:
            item_edit_allowed = False

        if isinstance(item, ModelWithCategory):
            item.has_categories = True
            item.set_category_lists_init_kwargs({'show_title': True, 'cat_html_class': 'label label-default'})

        # Нарочно передаём item под двумя разными именами.
        # Требуется для упрощения наслования шаблонов.
        context = {
            self.realm.name: item,
            'item': item,
            'item_edit_allowed': item_edit_allowed,
            'item_rating_allowed': item_rating_allowed
        }
        self.update_context(context, request)
        return self.render(request, context)


class TagsView(ListingView):
    """Список меток (категорий) для объекта."""

    def get_paginator_objects(self):
        return self.realm.model.get_objects_in_category(self.kwargs['category_id'])

    def get_most_voted_objects(self):
        return self.realm.model.get_most_voted_objects_in_category(self.kwargs['category_id'])


class EditView(RealmView):
    """Редактирование (и добавление) объекта."""

    @method_decorator(login_required)  # На страницах редактирования требуется атворизация.
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def preview_rst(self, request, text_src, xross=None):
        """Используется xross. Обрабатывает запрос на предварительный просмотр текста в формате rst.

        :param request:
        :param text_src:
        :param xross:
        :return:
        """
        item = xross.attrs['item']
        if item is None or isinstance(item, ModelWithCompiledText):
            return HttpResponse(ModelWithCompiledText.compile_text(text_src))

    def update_context(self, context, request):
        """Используется для дополнения контекста шаблона данными.

        :param dict context:
        :param Request request:
        :return:
        """

    @xross_view(preview_rst)
    def get(self, request, obj_id=None):
        item = None

        if obj_id is not None:
            item = self.get_object_or_404(obj_id)

        data = None
        if 'pythonz_form' in request.POST:
            data = request.POST

        form = self.realm.form(data, request.FILES or None, instance=item, user=request.user)
        if item is None:
            form.submit_title = self.realm.txt_form_add
        else:
            self.check_edit_permissions(request, item)
            form.submit_title = self.realm.txt_form_edit

        xross_listener(http_method='POST', item=item)

        from sitecats.toolbox import get_category_aliases_under
        if isinstance(item, ModelWithCategory):
            item.has_categories = True
            category_handled = item.enable_category_lists_editor(
                request,
                additional_parents_aliases=get_category_aliases_under(),
                handler_init_kwargs={'error_messages_extra_tags': 'alert alert-danger'},
                lists_init_kwargs={'show_title': True, 'cat_html_class': 'label label-default'},
                editor_init_kwargs={
                    'allow_add': True, 'allow_new': request.user.is_superuser, 'allow_remove': True,
                    'category_separator': ', '
                }
            )

            if category_handled:  # Добавилась категория, перенаправим на эту же страницу.
                return redirect(self.realm.get_edit_urlname(), item.id, permanent=True)

        show_modetation_hint = self.realm.model not in (User, Article, Discussion, Community, Event)

        if data is None:
            if show_modetation_hint:
                message_warning(
                    request, 'Обратите внимание, что на данном этапе развития проекта добавляемые '
                             'материалы проходят модерацию, прежде чем появиться на сайте.'
                )

        if item is None:
            redirector = lambda: redirect(item, permanent=True)
        else:
            redirector = lambda: redirect(self.realm.get_edit_urlname(), item.id, permanent=True)

        if form.is_valid():

            try:
                if item is None:
                    form.instance.submitter = request.user
                    item = form.save()
                    message_success(request, 'Объект добавлен.')
                    if show_modetation_hint:
                        message_info(request, 'Данный объект появится на сайте после модерации.')
                else:
                    form.instance.last_editor = request.user
                    form.save()
                    message_success(request, 'Данные сохранены.')

                return redirector()

            except PythonzException as e:
                message_error(request, e.message)

        context = {'form': form, self.realm.name: item, 'item': item}

        try:
            self.update_context(context, request)
        except RedirectRequired:
            return redirector()

        return self.render(request, context)


class AddView(EditView):
    """Добавление объекта."""

    @classmethod
    def get_template_path(cls, name=None):
        return super().get_template_path('edit')
