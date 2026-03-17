from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import CorruptionEntry, EntryMedia



# Create your views here.
def home(request):
    entries_list = CorruptionEntry.objects.prefetch_related('media').order_by('-id')
    paginator = Paginator(entries_list, 10)  # 10 entries per page
    page_number = request.GET.get('page')
    entries = paginator.get_page(page_number)
    
    return render(request, 'core/home.html', {'entries': entries})

@require_http_methods(["GET", "POST"])
def post_corruption(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        media_files = request.FILES.getlist('media_files')

        errors = {}

        if not title:
            errors['title'] = 'Title is required.'
        elif len(title) > 256:
            errors['title'] = 'Title must be 256 characters or fewer.'

        if not description:
            errors['description'] = 'Description is required.'

        ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
        ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'}
        ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB per file

        invalid_files = []
        oversized_files = []
        for f in media_files:
            if f.content_type not in ALLOWED_TYPES:
                invalid_files.append(f.name)
            elif f.size > MAX_FILE_SIZE:
                oversized_files.append(f.name)

        if invalid_files:
            errors['media'] = f"Unsupported file type(s): {', '.join(invalid_files)}"
        if oversized_files:
            errors['media'] = f"File(s) exceed 100MB limit: {', '.join(oversized_files)}"

        if errors:
            # Pass errors and repopulate form values
            context = {
                'form': _build_form_context(title, description, errors)
            }
            return render(request, 'core/post_corruption.html', context)

        # Save entry
        entry = CorruptionEntry.objects.create(
            title=title,
            description=description,
        )

        for f in media_files:
            if f.content_type in ALLOWED_IMAGE_TYPES:
                media_type = EntryMedia.IMAGE
            else:
                media_type = EntryMedia.VIDEO

            EntryMedia.objects.create(
                entry=entry,
                media_type=media_type,
                file=f,
            )

        messages.success(request, 'Your report has been submitted anonymously.')
        return redirect('home')

    return render(request, 'core/post_corruption.html', {'form': _build_form_context()})


def _build_form_context(title='', description='', errors=None):
    """
    Simple dict-based form context so the template doesn't need a Django Form class.
    Keeps the view lean while still supporting error display and value repopulation.
    """
    class _Field:
        def __init__(self, value, error):
            self.value = value
            self.errors = [error] if error else []

        def __str__(self):
            return self.value or ''

    class _Form:
        def __init__(self, title, description, errors):
            e = errors or {}
            self.title       = _Field(title,       e.get('title'))
            self.description = _Field(description, e.get('description'))
            self.media       = _Field('',           e.get('media'))
            self._non_field  = []

        def non_field_errors(self):
            return self._non_field

    return _Form(title, description, errors)