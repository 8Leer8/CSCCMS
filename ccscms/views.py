from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.views import View
from datetime import date
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings

import json
import logging
from django.utils import timezone
import openpyxl
from django.apps import apps
from django.template.loader import render_to_string
from io import BytesIO
from django.utils.html import strip_tags
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


logger = logging.getLogger(__name__)

from .models import (
    Account, User, Admin, Post, Event, Announcement, Complaint, Feedback,
    Achievement, Accomplishment, AuditLog, Volunteer, Officer, OfficerMember,
    EventLabel, EventType, EventLabelList, EventTypeList, EventAudience, Audience,
    Status, Category, College, Department, Position, Committee, CommitteeMember,
    Faculty, ComplaintType, Transparency, GalleryPost, GalleryPostImage,
    PostImage, AccomplishmentImage, AchievementImage, AnnouncementAudience, 
    FeedbackType
)

def is_admin(user):
    """Check if user is an admin"""
    return hasattr(user, 'admin')

class AuthView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('admin_dashboard')
            return redirect('landing_page')
        return render(request, 'auth/login.html')

    def post(self, request):
        if 'login' in request.POST:
            email = request.POST.get('email')
            password = request.POST.get('password')
            next_url = request.POST.get('next', '')
            
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if next_url:
                    return redirect(next_url)
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('landing_page')
            else:
                messages.error(request, 'Invalid email or password')
                return redirect('auth')
                
        elif 'signup' in request.POST:
            email = request.POST.get('email')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            contact_number = request.POST.get('contact_number')
            next_url = request.POST.get('next', '')
            
            if password != password2:
                messages.error(request, 'Passwords do not match')
                return redirect('auth')
                
            if User.objects.filter(account__email=email).exists():
                messages.error(request, 'Email already exists')
                return redirect('auth')
                
            # Create the Account first
            account = Account.objects.create_user(
                email=email,
                password=password,
                firstname=firstname,
                lastname=lastname,
                contact_number=contact_number,
                account_type='user',
                is_active=True
            )
            # Create the User and link to Account
            user = User.objects.create(
                account=account,
                username=email
            )
            # If you have a Profile model, update as needed
            # Profile.objects.create(user=user, contact_number=contact_number)
            
            login(request, account)
            if next_url:
                return redirect(next_url)
            return redirect('landing')
            
        return redirect('auth')

@login_required
def logout_view(request):
    user = request.user
    logout(request)
    messages.success(request, f'Goodbye, {user.firstname}! You have been logged out.')
    return redirect('auth')

@login_required
@user_passes_test(is_admin, login_url='landing_page')
def admin_dashboard(request):
    
    print(f"Requested page: {request.GET.get('page', 'dashboard')}")
    print(f"Is AJAX: {request.headers.get('x-requested-with') == 'XMLHttpRequest'}")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        page = request.GET.get('page', 'dashboard')

        try:
            if page == 'dashboard':
                html = render_to_string('admin/dashboard.html', request=request)
                data = get_dashboard_data(request)
                return JsonResponse({'html': html, 'data': data})

            elif page == 'events':
                events = Event.objects.filter(is_active=True).order_by('-date_event')
                paginator = Paginator(events, 5)
                page_number = request.GET.get('page', 1)
                page_obj = paginator.get_page(page_number)

                events_data = [
                    {
                        'id': event.id,
                        'name': event.name,
                        'date_event': event.date_event.strftime("%Y-%m-%d"),
                        'location': event.location,
                        'status': event.status,
                    }
                    for event in page_obj
                ]

                html = render_to_string('admin/event/event_list.html', {'events': page_obj}, request=request)
                return JsonResponse({
                    'html': html,
                    'data': {
                        'events': events_data,
                        'has_previous': page_obj.has_previous(),
                        'has_next': page_obj.has_next(),
                        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
                        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                        'current_page': page_obj.number,
                        'total_pages': paginator.num_pages,
                    }
                })

            elif page == 'event_form':
                html = render_to_string('admin/event/event_form.html', request=request)
                return HttpResponse(html)
            elif page == 'categories':
                html = render_to_string('admin/categories/categories_management.html', request=request)
                return JsonResponse({'html': html})
            elif page == 'posts':
                posts = Post.objects.filter(is_active=True).order_by('-created_at')
                paginator = Paginator(posts, 10)  # Or however many per page
                page_number = request.GET.get('post_page', 1)  # Use a different param if needed
                page_obj = paginator.get_page(page_number)
            
                posts_data = [
                    {
                        'id': post.id,
                        'title': post.title,
                        'category': post.category.category if post.category else "",
                        'status': post.status,
                        'created_at': post.created_at.strftime("%Y-%m-%d"),
                    }
                    for post in page_obj
                ]
            
                html = render_to_string('admin/post/post_list.html', {'posts': page_obj}, request=request)
                return JsonResponse({
                    'html': html,
                    'data': {
                        'posts': posts_data,
                        'has_previous': page_obj.has_previous(),
                        'has_next': page_obj.has_next(),
                        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
                        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                        'current_page': page_obj.number,
                        'total_pages': paginator.num_pages,
                    }
                })

            elif page == 'post_form':
                html = render_to_string('admin/post/post_form_modal.html', request=request)
                return HttpResponse(html)
            elif page == 'announcements':
                html = render_to_string('admin/announcement/announcement_list.html', request=request)
                return JsonResponse({'html': html})
            elif page == 'announcement_form':
                html = render_to_string('admin/announcement/announcement_form.html', request=request)
                return HttpResponse(html)
            # In your admin_dashboard view, add this condition:
            elif page == 'achievements':
                html = render_to_string('admin/achievement/achievement_list.html', request=request)
                return JsonResponse({'html': html})
            
            elif page == 'achievement_form':
                html = render_to_string('admin/achievement/achievement_form.html', request=request)
                return HttpResponse(html)
            elif page == 'accomplishments':
                html = render_to_string('admin/accomplishment/accomplishment_list.html', {
                    'categories': Category.objects.filter(is_active=True, scope_id__in=[4, 7])
                }, request=request)
                return JsonResponse({'html': html})
            elif page == 'accomplishment_form':
                html = render_to_string('admin/accomplishment/accomplishment_form.html', request=request)
                return HttpResponse(html)
            elif page == 'accounts':
                html = render_to_string('admin/account/account_list.html', request=request)
                return JsonResponse({'html': html})
            elif page == 'account_form':
                html = render_to_string('admin/account/account_form_modal.html', request=request)
                return HttpResponse(html)
            elif page == 'transparency':
                html = render_to_string('admin/transparency/transparency_list.html', request=request)
                return JsonResponse({'html': html})
            elif page == 'transparency_form':
                html = render_to_string('admin/transparency/transparency_form.html', request=request)
                return HttpResponse(html)
            else:
                return JsonResponse({'error': f'Page "{page}" not found'}, status=404)
        except Exception as e:
            logger.error(f"Error in admin_dashboard view: {e}", exc_info=True)
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return render(request, 'admin/base.html')

def get_dashboard_data(request):
    try:
        # Get counts for dashboard cards
        total_posts = Post.objects.filter(is_active=True).count()
        total_events = Event.objects.filter(is_active=True).count()
        total_announcements = Announcement.objects.filter(is_active=True).count()
        pending_complaints = Complaint.objects.filter(is_active=True, remarks='pending').count()
        total_achievements = Achievement.objects.filter(is_active=True).count()
        total_volunteers = Volunteer.objects.filter(is_active=True).count()

        # Get latest records
        latest_posts = list(Post.objects.filter(is_active=True).order_by('-created_at')[:5].values(
            'id', 'title', 'context', 'created_at', 'category__category'
        ))
        latest_events = list(Event.objects.filter(is_active=True).order_by('-date_event')[:5].values(
            'id', 'name', 'context', 'date_event', 'start_at', 'status'
        ))
        latest_announcements = list(Announcement.objects.filter(is_active=True).order_by('-created_at')[:5].values(
            'id', 'title', 'context', 'start_publish_on', 'category__category'
        ))
        latest_complaints = list(Complaint.objects.filter(is_active=True).order_by('-created_at')[:5].values(
            'id', 'complaint_type__type', 'description', 'created_at', 'remarks'
        ))
        latest_achievements = list(Achievement.objects.filter(is_active=True).order_by('-awarded_on')[:5].values(
            'id', 'title', 'awarded_by', 'awarded_on', 'category__category'
        ))
        latest_accomplishments = list(Accomplishment.objects.filter(is_active=True).order_by('-accomplish_on')[:5].values(
            'id', 'title', 'context', 'accomplish_on', 'category__category'
        ))

        # Get latest accounts (only users, exclude admins)
        latest_accounts = list(Account.objects.filter(
            is_active=True, account_type='user'
        ).order_by('-created_at')[:5].values(
            'id', 'email', 'firstname', 'lastname', 'account_type', 'created_at'
        ))

        # Prepare data for charts
        posts_by_category = list(
            Post.objects.filter(is_active=True)
            .values('category__category')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        events_by_status = list(
            Event.objects.filter(is_active=True)
            .values('status')
            .annotate(count=Count('id'))
        )

        complaints_by_status = list(
            Complaint.objects.filter(is_active=True)
            .values('remarks')
            .annotate(count=Count('id'))
        )

        # Time series for line charts (last 6 months)
        from django.utils import timezone
        from django.db.models.functions import TruncMonth
        now = timezone.now()
        six_months_ago = now - timedelta(days=180)

        posts_time_series = list(
            Post.objects.filter(is_active=True, created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        events_time_series = list(
            Event.objects.filter(is_active=True, date_event__gte=six_months_ago)
            .annotate(month=TruncMonth('date_event'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        complaints_time_series = list(
            Complaint.objects.filter(is_active=True, created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        return {
            'total_posts': total_posts,
            'total_events': total_events,
            'total_announcements': total_announcements,
            'pending_complaints': pending_complaints,
            'total_achievements': total_achievements,
            'total_volunteers': total_volunteers,

            'latest_posts': latest_posts,
            'latest_events': latest_events,
            'latest_announcements': latest_announcements,
            'latest_complaints': latest_complaints,
            'latest_achievements': latest_achievements,
            'latest_accomplishments': latest_accomplishments,
            'latest_accounts': latest_accounts,

            'posts_by_category': posts_by_category,
            'events_by_status': events_by_status,
            'complaints_by_status': complaints_by_status,
            'posts_time_series': posts_time_series,
            'events_time_series': events_time_series,
            'complaints_time_series': complaints_time_series,
        }
    except Exception as e:
        logger.error(f"Error in get_dashboard_data: {e}", exc_info=True)
        return {}


def client_lpage(request):
    return redirect('landing_page')

class EventListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_admin(self.request.user)
        
    def get(self, request):
        # Convert show_deleted string to boolean properly
        show_deleted = request.GET.get('show_deleted', 'false').lower() == 'true'
        
        # Use all_objects manager to get both active and inactive events
        if show_deleted:
            events = Event.all_objects.filter(is_active=False)
        else:
            events = Event.objects.filter(is_active=True)
        
        status = request.GET.get('status')
        if status:
            events = events.filter(status=status)
        
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        if date_from and date_to:
            events = events.filter(date_event__range=[date_from, date_to])
        
        # Add support for single event_date filter
        event_date = request.GET.get('event_date')
        if event_date:
            events = events.filter(date_event=event_date)
            
        search = request.GET.get('search')
        if search:
            events = events.filter(
                Q(name__icontains=search) |
                Q(location__icontains=search) |
                Q(description__icontains=search)
            )
            
        # Filter by category selections
        label_ids = request.GET.get('labels')
        if label_ids:
            label_ids = [int(i) for i in label_ids.split(',') if i.isdigit()]
            if label_ids:
                events = events.filter(labels__id__in=label_ids)
        type_ids = request.GET.get('types')
        if type_ids:
            type_ids = [int(i) for i in type_ids.split(',') if i.isdigit()]
            if type_ids:
                events = events.filter(types__id__in=type_ids)
        audience_ids = request.GET.get('audiences')
        if audience_ids:
            audience_ids = [int(i) for i in audience_ids.split(',') if i.isdigit()]
            if audience_ids:
                events = events.filter(audiences__id__in=audience_ids)
                
        # Order events by date
        events = events.order_by('-date_event')
        
        # Pagination
        paginator = Paginator(events, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        events_data = []
        for event in page_obj:
            labels = list(event.labels.values_list('type', flat=True))
            types = list(event.types.values_list('type', flat=True))
            audiences = list(event.audiences.values_list('type', flat=True))
            event_data = {
                'id': event.id,
                'name': event.name,
                'date_event': event.date_event.strftime("%Y-%m-%d") if event.date_event else None,
                'location': event.location,
                'status': event.status,
                'event_img': request.build_absolute_uri(event.event_img.url) if event.event_img else None,
                'context': event.context,
                'description': event.description,
                'start_at': event.start_at.strftime("%H:%M") if event.start_at else None,
                'end_at': event.end_at.strftime("%H:%M") if event.end_at else None,
                'start_publish_on': event.start_publish_on.strftime("%Y-%m-%d") if event.start_publish_on else None,
                'end_publish_on': event.end_publish_on.strftime("%Y-%m-%d") if event.end_publish_on else None,
                'labels': labels,
                'types': types,
                'audiences': audiences,
                'is_active': event.is_active,
                'is_deleted': not event.is_active
            }
            events_data.append(event_data)
            
        # Add pagination info for frontend
        start_index = page_obj.start_index() if events_data else 0
        end_index = page_obj.end_index() if events_data else 0
        total_items = paginator.count
        
        return JsonResponse({
            'events': events_data,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'start_index': start_index,
            'end_index': end_index,
            'total_items': total_items
        })

class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_admin(self.request.user)

    def post(self, request):
        try:
            # Print received data for debugging
            print("POST data:", request.POST)
            print("FILES:", request.FILES)

            # Map form field names to model field names
            field_map = {
                'eventName': 'name',
                'eventDate': 'date_event',
                'eventStartTime': 'start_at',
                'eventEndTime': 'end_at',
                'eventLocation': 'location',
                'eventContext': 'context',
                'eventDescription': 'description',
                'eventLandmark': 'landmark',
                'eventPublishStart': 'start_publish_on',
                'eventPublishEnd': 'end_publish_on'
            }

            # Prepare data dictionary
            data = {}
            missing_fields = []
            
            for form_field, model_field in field_map.items():
                value = request.POST.get(form_field)
                if form_field in ['eventName', 'eventDate', 
                                 'eventStartTime', 'eventEndTime', 'eventLocation',
                                 'eventContext', 'eventDescription'] and not value:
                    missing_fields.append(form_field)
                data[model_field] = value

            if missing_fields:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields,
                    'message': 'The following fields are required: ' + ', '.join(missing_fields)
                }, status=400)

            # Convert date and time fields
            try:
                if data['date_event']:
                    data['date_event'] = datetime.strptime(data['date_event'], '%Y-%m-%d').date()
                if data['start_at']:
                    data['start_at'] = datetime.strptime(data['start_at'], '%H:%M').time()
                if data['end_at']:
                    data['end_at'] = datetime.strptime(data['end_at'], '%H:%M').time()
                
                if data.get('start_publish_on'):
                    data['start_publish_on'] = datetime.strptime(data['start_publish_on'], '%Y-%m-%d').date()
                if data.get('end_publish_on'):
                    data['end_publish_on'] = datetime.strptime(data['end_publish_on'], '%Y-%m-%d').date()
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid date or time format',
                    'message': f'Error parsing date/time: {str(e)}'
                }, status=400)

            # Set status based on publish start date
            today = timezone.now().date()
            if data.get('start_publish_on'):
                data['status'] = 'scheduled' if data['start_publish_on'] > today else 'active'
            else:
                data['status'] = 'active'

            # Create the event
            event = Event.objects.create(
                admin=request.user.admin,
                name=data['name'],
                context=data['context'],
                description=data['description'],
                event_img=request.FILES.get('eventFeaturedImage'),
                landmark=data.get('landmark'),
                location=data['location'],
                start_at=data['start_at'],
                end_at=data['end_at'],
                date_event=data['date_event'],
                status=data['status'],
                start_publish_on=data.get('start_publish_on'),
                end_publish_on=data.get('end_publish_on')
            )

            # Process many-to-many relationships
            for label_id in request.POST.getlist('eventLabels', []):
                if label_id:
                    EventLabelList.objects.create(event=event, event_label_id=label_id)

            for type_id in request.POST.getlist('eventTypes', []):
                if type_id:
                    EventTypeList.objects.create(event=event, event_type_id=type_id)

            for audience_id in request.POST.getlist('eventAudiences', []):
                if audience_id:
                    EventAudience.objects.create(event=event, audience_id=audience_id)

            return JsonResponse({
                'success': True, 
                'id': event.id,
                'message': 'Event created successfully!'
            })
            
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e),
                'message': f'Server error while creating event: {str(e)}'
            }, status=500)


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        """Test that the user is an admin"""
        return is_admin(self.request.user)

    def get(self, request, pk):
        try:
            event = Event.objects.get(pk=pk, is_active=True)
            
            # Get related many-to-many data
            labels = list(event.labels.values_list('id', flat=True))
            types = list(event.types.values_list('id', flat=True))
            audiences = list(event.audiences.values_list('id', flat=True))
            
            data = {
                'success': True,
                'event': {
                    'id': event.id,
                    'name': event.name,
                    'status': event.status,
                    'date_event': event.date_event.strftime('%Y-%m-%d') if event.date_event else None,
                    'start_at': event.start_at.strftime('%H:%M') if event.start_at else None,
                    'end_at': event.end_at.strftime('%H:%M') if event.end_at else None,
                    'location': event.location,
                    'landmark': event.landmark,
                    'context': event.context,
                    'description': event.description,
                    'start_publish_on': event.start_publish_on.strftime('%Y-%m-%d') if event.start_publish_on else None,
                    'end_publish_on': event.end_publish_on.strftime('%Y-%m-%d') if event.end_publish_on else None,
                    'event_img': request.build_absolute_uri(event.event_img.url) if event.event_img else None,
                    'labels': labels,
                    'types': types,
                    'audiences': audiences,
                }
            }
            
            return JsonResponse(data, encoder=DjangoJSONEncoder)
            
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Event not found'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk, is_active=True)
            
            # Map form field names to model field names
            field_map = {
                'eventName': 'name',
                'eventDate': 'date_event',
                'eventStartTime': 'start_at',
                'eventEndTime': 'end_at',
                'eventLocation': 'location',
                'eventContext': 'context',
                'eventDescription': 'description',
                'eventLandmark': 'landmark',
                'eventPublishStart': 'start_publish_on',
                'eventPublishEnd': 'end_publish_on'
            }

            # Update basic fields
            for form_field, model_field in field_map.items():
                value = request.POST.get(form_field)
                if value is not None:
                    if model_field in ['date_event', 'start_publish_on', 'end_publish_on']:
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    elif model_field in ['start_at', 'end_at']:
                        value = datetime.strptime(value, '%H:%M').time()
                    setattr(event, model_field, value)

            # Update image if provided
            if 'eventFeaturedImage' in request.FILES:
                event.event_img = request.FILES['eventFeaturedImage']

            # Save the event
            event.save()

            # Update many-to-many relationships
            # First, clear existing relationships
            event.labels.clear()
            event.types.clear()
            event.audiences.clear()

            # Then add new relationships
            for label_id in request.POST.getlist('eventLabels', []):
                if label_id:
                    EventLabelList.objects.create(event=event, event_label_id=label_id)

            for type_id in request.POST.getlist('eventTypes', []):
                if type_id:
                    EventTypeList.objects.create(event=event, event_type_id=type_id)

            for audience_id in request.POST.getlist('eventAudiences', []):
                if audience_id:
                    EventAudience.objects.create(event=event, audience_id=audience_id)

            return JsonResponse({
                'success': True,
                'message': 'Event updated successfully!'
            })

        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Event not found'
            }, status=404)
            
        except Exception as e:
            logger.error(f"Error updating event: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': f'Server error while updating event: {str(e)}'
            }, status=500)

class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_admin(self.request.user)

    def post(self, request, pk):
        try:
            event = get_object_or_404(Event, pk=pk, is_active=True)
            event.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

def get_event_form_data(request):
    try:
        event_labels = list(EventLabel.all_objects.filter(is_active=True).values('id', 'type'))
        event_types = list(EventType.all_objects.filter(is_active=True).values('id', 'type'))
        audiences = list(Audience.all_objects.filter(is_active=True).values('id', 'type'))
        
        return JsonResponse({
            'success': True,
            'event_labels': event_labels,
            'event_types': event_types,
            'audiences': audiences,
        })
    except Exception as e:
        logger.error(f"Error getting event form data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

class EventRestoreView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_admin(self.request.user)

    def post(self, request, pk):
        try:
            event = get_object_or_404(Event.all_objects, pk=pk, is_active=False)
            event.is_active = True  # Restore
            event.save()
            
            # Log the restoration
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='Event',
                record_id=event.id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return JsonResponse({'success': True, 'message': 'Event restored successfully'})
        except Exception as e:
            logger.error(f"Error restoring event: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

class EventPermanentDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_admin(self.request.user)

    def post(self, request, pk):
        try:
            event = get_object_or_404(Event, pk=pk, is_active=False)
            
            # Log the deletion before actually deleting
            AuditLog.objects.create(
                user=request.user,
                action='delete',
                model_name='Event',
                record_id=event.id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            event.delete()  # This will do a hard delete
            
            return JsonResponse({'success': True, 'message': 'Event permanently deleted'})
        except Exception as e:
            logger.error(f"Error permanently deleting event: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

def categories_management(request):
    # Determine active tab from request (default to labels)
    active_tab = request.GET.get('tab', 'labels')
    
    context = {
        'active_tab': active_tab,
        # Add any other context data needed for all tabs
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return just the content for the requested tab
        template_name = f'admin/categories/event_{active_tab}.html'
        html = render_to_string(template_name, context)
        return JsonResponse({'html': html})
    
    # Regular request - render full page
    return render(request, 'admin/categories/categories_management.html', context)
        
@login_required
@user_passes_test(is_admin)
def manage_labels(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return just the content
        labels = EventLabel.objects.all()
        context = {'labels': labels}
        html = render_to_string('admin/categories/event_labels.html', context)
        return JsonResponse({'html': html})
    else:
        # Full page request - render normally
        return render(request, 'admin/categories/categories_management.html', {
            'active_tab': 'labels'
        })

@login_required
@user_passes_test(is_admin)
def manage_types(request):
    types = EventType.objects.filter(is_active=True)
    return render(request, 'admin/categories/event_type.html', {'types': types})

@login_required
@user_passes_test(is_admin)
def manage_audiences(request):
    audiences = Audience.objects.filter(is_active=True)
    return render(request, 'admin/categories/target_audience.html', {'audiences': audiences})

# AJAX Views for Categories
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def ajax_labels(request):
    try:
        labels = EventLabel.objects.filter(is_active=True)
        html = render_to_string('admin/categories/event_labels.html', {'labels': labels})
        data = list(labels.values('id', 'type', 'description', 'is_active'))
        return JsonResponse({'success': True, 'html': html, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@login_required
@user_passes_test(is_admin)
def ajax_types(request):
    types = list(EventType.objects.filter(is_active=True).values('id', 'type', 'description', 'is_active'))
    return JsonResponse({'data': types})

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def ajax_audiences(request):
    audiences = list(Audience.objects.filter(is_active=True).values('id', 'type', 'description', 'is_active'))
    return JsonResponse({'data': audiences})

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def ajax_create_category(request):
    try:
        data = json.loads(request.body)
        category_type = data.get('category_type')
        type_name = data.get('type')
        description = data.get('description', '')
        is_active = data.get('is_active', True)
        
        # Validate required fields
        if not category_type or not type_name:
            return JsonResponse({
                'success': False, 
                'error': 'Category type and name are required'
            }, status=400)
            
        # Validate category type
        if category_type not in ['label', 'type', 'audience']:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid category type'
            }, status=400)
            
        # Check for duplicate names
        if category_type == 'label' and EventLabel.objects.filter(type=type_name).exists():
            return JsonResponse({
                'success': False,
                'error': 'A label with this name already exists'
            }, status=400)
        elif category_type == 'type' and EventType.objects.filter(type=type_name).exists():
            return JsonResponse({
                'success': False,
                'error': 'A type with this name already exists'
            }, status=400)
        elif category_type == 'audience' and Audience.objects.filter(type=type_name).exists():
            return JsonResponse({
                'success': False,
                'error': 'An audience with this name already exists'
            }, status=400)
        
        if category_type == 'label':
            obj = EventLabel.objects.create(
                type=type_name,
                description=description,
                is_active=is_active
            )
        elif category_type == 'type':
            obj = EventType.objects.create(
                type=type_name,
                description=description,
                is_active=is_active
            )
        elif category_type == 'audience':
            obj = Audience.objects.create(
                type=type_name,
                description=description,
                is_active=is_active
            )
            
        return JsonResponse({
            'success': True,
            'id': obj.id,
            'type': obj.type,
            'description': obj.description,
            'is_active': obj.is_active
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def ajax_update_category(request):
    try:
        data = json.loads(request.body)
        category_type = data.get('category_type')
        item_id = data.get('id')
        type_name = data.get('type')
        description = data.get('description', '')
        is_active = data.get('is_active', True)
        
        # Validate required fields
        if not category_type or not type_name or not item_id:
            return JsonResponse({
                'success': False,
                'error': 'Category type, name, and ID are required'
            }, status=400)
            
        # Validate category type
        if category_type not in ['label', 'type', 'audience']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid category type'
            }, status=400)
            
        # Get the object
        try:
            if category_type == 'label':
                obj = EventLabel.objects.get(pk=item_id)
            elif category_type == 'type':
                obj = EventType.objects.get(pk=item_id)
            elif category_type == 'audience':
                obj = Audience.objects.get(pk=item_id)
        except (EventLabel.DoesNotExist, EventType.DoesNotExist, Audience.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Category not found'
            }, status=404)
            
        # Check for duplicate names (excluding current item)
        if category_type == 'label' and EventLabel.objects.exclude(pk=item_id).filter(type=type_name).exists():
            return JsonResponse({
                'success': False,
                'error': 'A label with this name already exists'
            }, status=400)
        elif category_type == 'type' and EventType.objects.exclude(pk=item_id).filter(type=type_name).exists():
            return JsonResponse({
                'success': False,
                'error': 'A type with this name already exists'
            }, status=400)
        elif category_type == 'audience' and Audience.objects.exclude(pk=item_id).filter(type=type_name).exists():
            return JsonResponse({
                'success': False,
                'error': 'An audience with this name already exists'
            }, status=400)
            
        obj.type = type_name
        obj.description = description
        obj.is_active = is_active
        obj.save()
        
        return JsonResponse({
            'success': True,
            'id': obj.id,
            'type': obj.type,
            'description': obj.description,
            'is_active': obj.is_active
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def ajax_delete_category(request):
    try:
        data = json.loads(request.body)
        category_type = data.get('category_type')
        item_id = data.get('id')
        
        if category_type == 'label':
            obj = get_object_or_404(EventLabel, pk=item_id)
        elif category_type == 'type':
            obj = get_object_or_404(EventType, pk=item_id)
        elif category_type == 'audience':
            obj = get_object_or_404(Audience, pk=item_id)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid category type'}, status=400)
            
        obj.delete()  # Soft delete
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Helper function to get client IP
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Post List View (AJAX)
@login_required
@user_passes_test(is_admin)
def post_list(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Get filter parameters
            status = request.GET.get('status', '')
            category = request.GET.get('category', '')
            search = request.GET.get('search', '')
            page = request.GET.get('page', 1)
            
            # Start with base queryset with select_related for foreign keys
            posts = Post.objects.filter(is_active=True).select_related(
                'category', 'admin', 'admin__account'
            ).prefetch_related('images').order_by('-created_at')
            
            # Apply filters
            if status:
                posts = posts.filter(status=status)
            if category:
                posts = posts.filter(category_id=category)
            if search:
                posts = posts.filter(
                    Q(title__icontains=search) |
                    Q(content__icontains=search) |
                    Q(context__icontains=search)
                )

            # Pagination
            paginator = Paginator(posts, 10)
            page_obj = paginator.get_page(page)
            
            # Prepare data for response
            posts_data = []
            for post in page_obj:
                posts_data.append({
                    'id': post.id,
                    'title': post.title,
                    'category': post.category.category if post.category else 'Uncategorized',
                    'category_id': post.category.id if post.category else None,
                    'status': post.status,
                    'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
                    'start_publish_on': post.start_publish_on.strftime('%Y-%m-%d') if post.start_publish_on else None,
                    'end_publish_on': post.end_publish_on.strftime('%Y-%m-%d') if post.end_publish_on else None,
                    'author': f"{post.admin.account.firstname} {post.admin.account.lastname}",
                    'featured_image': post.images.first().image.url if post.images.exists() else None,
                })
            
            # Get categories for filter dropdown
            categories = Category.objects.filter(is_active=True).values('id', 'category')
            
            return JsonResponse({
                'success': True,
                'posts': posts_data,
                'categories': list(categories),
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'start_index': (page_obj.number - 1) * paginator.per_page + 1,
                'end_index': min(page_obj.number * paginator.per_page, paginator.count),
            })
        except Exception as e:
            logger.error(f"Error in post_list: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


# Post Create View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def post_create(request):
    if request.method == 'POST':
        try:
            # Get data from request
            data = request.POST.dict()
            
            # Validate required fields
            required_fields = ['title', 'content', 'context']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'error': f'{field} is required'
                    }, status=400)

            # Parse dates safely
            def parse_date(date_str):
                if not date_str:
                    return None
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return None

            start_publish = parse_date(data.get('start_publish_on'))
            end_publish = parse_date(data.get('end_publish_on'))

            # Validate publish dates if provided
            if start_publish and end_publish and start_publish > end_publish:
                return JsonResponse({
                    'success': False,
                    'error': 'End publish date must be after start date'
                }, status=400)

            # Create the post
            post = Post.objects.create(
                title=data['title'],
                content=data['content'],
                context=data['context'],
                category_id=data.get('category'),
                status=data.get('status', 'draft'),
                admin=request.user.admin,
                start_publish_on=start_publish,
                end_publish_on=end_publish
            )

            # Handle images
            if 'images' in request.FILES:
                for image in request.FILES.getlist('images'):
                    PostImage.objects.create(post=post, image=image)

            return JsonResponse({
                'success': True,
                'post_id': post.id,
                'message': 'Post created successfully'
            })

        except Exception as e:
            logger.error(f"Error creating post: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)
    
# Post Update View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def post_update(request, pk):
    if request.method == 'POST':
        try:
            post = get_object_or_404(Post, pk=pk, is_active=True)
            data = request.POST.dict()

            # Parse dates safely
            def parse_date(date_str):
                if not date_str:
                    return None
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return None

            start_publish = parse_date(data.get('start_publish_on'))
            end_publish = parse_date(data.get('end_publish_on'))

            # Validate publish dates if provided
            if start_publish and end_publish and start_publish > end_publish:
                return JsonResponse({
                    'success': False,
                    'error': 'End publish date must be after start date'
                }, status=400)

            # Update fields
            post.title = data.get('title', post.title)
            post.content = data.get('content', post.content)
            post.context = data.get('context', post.context)
            post.category_id = data.get('category', post.category_id)
            post.status = data.get('status', post.status)
            post.start_publish_on = start_publish
            post.end_publish_on = end_publish
            
            # Handle new images
            if 'images' in request.FILES:
                for image in request.FILES.getlist('images'):
                    PostImage.objects.create(post=post, image=image)

            post.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Post updated successfully'
            })
        except Exception as e:
            logger.error(f"Error updating post: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)
# Post Delete View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def post_delete(request, pk):
    if request.method == 'POST':
        try:
            post = get_object_or_404(Post, pk=pk, is_active=True)
            post.delete()  # Soft delete
            return JsonResponse({'success': True, 'message': 'Post deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

# Post Detail View (AJAX)
@login_required
@user_passes_test(is_admin)
def post_detail(request, pk):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            post = get_object_or_404(Post, pk=pk, is_active=True)
            
            # Get images if needed
            images = []
            for img in post.images.all():
                images.append({
                    'id': img.id,
                    'url': request.build_absolute_uri(img.image.url),
                    'created_at': img.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            return JsonResponse({
                'success': True,
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'content': post.content,
                    'context': post.context,
                    'category_id': post.category.id if post.category else None,
                    'category_name': post.category.category if post.category else '',
                    'status': post.status,
                    'start_publish_on': post.start_publish_on.strftime('%Y-%m-%d') if post.start_publish_on else None,
                    'end_publish_on': post.end_publish_on.strftime('%Y-%m-%d') if post.end_publish_on else None,
                    'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
                    'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M'),
                    'images': images
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

# Post Form Data (for dropdowns)
@login_required
@user_passes_test(is_admin)
def post_form_data(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            categories = list(Category.objects.filter(is_active=True, scope_id__in=[6, 7]).values('id', 'category'))
            if not categories:
                # Create a default category if none exists
                default_category = Category.objects.create(
                    category='General',
                    description='Default category for posts'
                )
                categories = [{'id': default_category.id, 'category': default_category.category}]
            
            status_choices = [{'value': val, 'label': label} for val, label in Post._meta.get_field('status').choices]
            
            return JsonResponse({
                'success': True,
                'categories': categories,
                'status_choices': status_choices
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


#announcement

# Announcement List View (AJAX)
@login_required
@user_passes_test(is_admin)
def announcement_list(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Get filter parameters
            status = request.GET.get('status', '')
            category = request.GET.get('category', '')
            search = request.GET.get('search', '')
            page = request.GET.get('page', 1)
            show_deleted = request.GET.get('show_deleted', 'false').lower() == 'true'
            
            # Start with base queryset
            if show_deleted:
                announcements = Announcement.all_objects.filter(is_active=False)
            else:
                announcements = Announcement.objects.filter(is_active=True)
            
            # Apply filters
            if status:
                announcements = announcements.filter(status=status)
            if category:
                announcements = announcements.filter(category_id=category)
            else:
                announcements = announcements.filter(category__scope_id__in=[1, 7])
            if search:
                announcements = announcements.filter(
                    Q(title__icontains=search) |
                    Q(content__icontains=search) |
                    Q(context__icontains=search))
                
            # Pagination
            paginator = Paginator(announcements.order_by('-created_at'), 10)
            page_obj = paginator.get_page(page)
            
            # Prepare data for response
            announcements_data = []
            for announcement in page_obj:
                announcements_data.append({
                    'id': announcement.id,
                    'title': announcement.title,
                    'category': announcement.category.category if announcement.category else '',
                    'status': announcement.status,
                    'start_publish_on': announcement.start_publish_on.strftime('%Y-%m-%d') if announcement.start_publish_on else '',
                    'end_publish_on': announcement.end_publish_on.strftime('%Y-%m-%d') if announcement.end_publish_on else '',
                    'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M'),
                    'is_active': announcement.is_active,
                    'image': announcement.image.url if announcement.image else None
                })
            
            # Get categories for filter dropdown (only scope_id 1 or 7)
            categories = list(Category.objects.filter(is_active=True, scope_id__in=[1, 7]).values('id', 'category'))
            # Insert 'All Categories' at the start
            categories.insert(0, {'id': '', 'category': 'All Categories'})
            
            return JsonResponse({
                'success': True,
                'announcements': announcements_data,
                'categories': categories,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'start_index': (page_obj.number - 1) * paginator.per_page + 1,
                'end_index': min(page_obj.number * paginator.per_page, paginator.count),
                'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            })
        except Exception as e:
            logger.error(f"Error in announcement_list: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    # For non-AJAX requests, render the template with categories context
    categories = Category.objects.filter(is_active=True, scope_id__in=[1, 7])
    return render(request, 'admin/announcement/announcement_list.html', {
        'categories': categories
    })

# Announcement Create View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def announcement_create(request):
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            image = request.FILES.get('image')

            # Validate required fields
            required_fields = ['title', 'content', 'context', 'category']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'error': f'{field} is required'
                    }, status=400)

            # Parse dates safely (allow None)
            def parse_date(date_str):
                if not date_str:
                    return None
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return None
            def parse_time(time_str):
                if not time_str:
                    return None
                try:
                    return datetime.strptime(time_str, '%H:%M').time()
                except ValueError:
                    return None

            start_publish = parse_date(data.get('start_publish_on'))
            end_publish = parse_date(data.get('end_publish_on'))
            date_post = parse_date(data.get('date_post'))
            time_post = parse_time(data.get('time_post'))

            # Create the announcement
            announcement = Announcement.objects.create(
                title=data['title'],
                content=data['content'],
                context=data['context'],
                category_id=data['category'],
                status=data.get('status', 'active'),  # Default to active
                admin=request.user.admin,
                start_publish_on=start_publish,  # Can be None
                end_publish_on=end_publish,      # Can be None
                date_post=date_post,             # Can be None
                time_post=time_post,             # Can be None
                landmark=data.get('landmark'),   # Can be None
                location=data.get('location'),   # Can be None
                image=image
            )

            # Handle audiences
            for audience_id in request.POST.getlist('audiences', []):
                if audience_id:
                    AnnouncementAudience.objects.create(
                        announcement=announcement,
                        audience_id=audience_id
                    )

            return JsonResponse({
                'success': True,
                'announcement_id': announcement.id,
                'message': 'Announcement created successfully'
            })

        except Exception as e:
            logger.error(f"Error creating announcement: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e),
                'message': f'Server error while creating announcement: {str(e)}'
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)
# Announcement Update View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def announcement_update(request, pk):
    if request.method == 'POST':
        try:
            announcement = get_object_or_404(Announcement, pk=pk, is_active=True)
            data = request.POST.dict()
            image = request.FILES.get('image')

            # Parse dates safely
            def parse_date(date_str):
                if not date_str:
                    return None
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return None
            def parse_time(time_str):
                if not time_str:
                    return None
                try:
                    return datetime.strptime(time_str, '%H:%M').time()
                except ValueError:
                    return None

            start_publish = parse_date(data.get('start_publish_on'))
            end_publish = parse_date(data.get('end_publish_on'))
            date_post = parse_date(data.get('date_post'))
            time_post = parse_time(data.get('time_post'))

            # Validate publish dates if provided
            if start_publish and end_publish and start_publish > end_publish:
                return JsonResponse({
                    'success': False,
                    'error': 'End publish date must be after start date'
                }, status=400)

            # Update fields
            announcement.title = data.get('title', announcement.title)
            announcement.content = data.get('content', announcement.content)
            announcement.context = data.get('context', announcement.context)
            announcement.category_id = data.get('category', announcement.category_id)
            announcement.status = data.get('status', announcement.status)
            announcement.start_publish_on = start_publish
            announcement.end_publish_on = end_publish
            announcement.date_post = date_post
            announcement.time_post = time_post
            announcement.landmark = data.get('landmark')
            announcement.location = data.get('location')
            if image:
                announcement.image = image

            # Update audiences
            if 'audiences' in request.POST:
                # Clear existing audiences
                AnnouncementAudience.objects.filter(announcement=announcement).delete()
                # Add new audiences
                for audience_id in request.POST.getlist('audiences', []):
                    if audience_id:
                        AnnouncementAudience.objects.create(
                            announcement=announcement,
                            audience_id=audience_id
                        )

            announcement.save()

            return JsonResponse({
                'success': True,
                'message': 'Announcement updated successfully'
            })
        except Exception as e:
            logger.error(f"Error updating announcement: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)

# Announcement Detail View (AJAX)
@login_required
@user_passes_test(is_admin)
def announcement_detail_admin(request, pk):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            announcement = get_object_or_404(Announcement, pk=pk)
            
            # Get selected audiences
            selected_audiences = list(announcement.audiences.values_list('id', flat=True))
            
            return JsonResponse({
                'success': True,
                'announcement': {
                    'id': announcement.id,
                    'title': announcement.title,
                    'content': announcement.content,
                    'context': announcement.context,
                    'category_id': announcement.category.id if announcement.category else None,
                    'category_name': announcement.category.category if announcement.category else '',
                    'status': announcement.status,
                    'start_publish_on': announcement.start_publish_on.strftime('%Y-%m-%d') if announcement.start_publish_on else None,
                    'end_publish_on': announcement.end_publish_on.strftime('%Y-%m-%d') if announcement.end_publish_on else None,
                    'date_post': announcement.date_post.strftime('%Y-%m-%d') if announcement.date_post else None,
                    'time_post': announcement.time_post.strftime('%H:%M') if announcement.time_post else None,
                    'landmark': announcement.landmark,
                    'location': announcement.location,
                    'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M'),
                    'updated_at': announcement.updated_at.strftime('%Y-%m-%d %H:%M'),
                    'selected_audiences': selected_audiences
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

# Announcement Delete View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def announcement_delete(request, pk):
    if request.method == 'POST':
        try:
            announcement = get_object_or_404(Announcement, pk=pk, is_active=True)
            announcement.delete()  # Soft delete
            return JsonResponse({'success': True, 'message': 'Announcement deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

# Announcement Restore View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def announcement_restore(request, pk):
    if request.method == 'POST':
        try:
            # Use all_objects to include soft-deleted announcements
            announcement = Announcement.all_objects.get(pk=pk)
            if announcement.is_active:
                return JsonResponse({'success': True, 'message': 'Announcement already active'})
            announcement.is_active = True
            announcement.save()
            return JsonResponse({'success': True, 'message': 'Announcement restored successfully'})
        except Announcement.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No Announcement matches the given query.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

# Announcement Permanent Delete View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def announcement_permanent_delete(request, pk):
    if request.method == 'POST':
        try:
            announcement = get_object_or_404(Announcement, pk=pk, is_active=False)
            announcement.delete()  # Hard delete
            return JsonResponse({'success': True, 'message': 'Announcement permanently deleted'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

# Announcement Form Data (for dropdowns)
@login_required
@user_passes_test(is_admin)
def announcement_form_data(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            categories = list(Category.objects.filter(is_active=True, scope_id__in=[1,7]).values('id', 'category'))
            audiences = list(Audience.objects.filter(is_active=True).values('id', 'type'))
            status_choices = [{'value': val, 'label': label} for val, label in Announcement._meta.get_field('status').choices]
            
            return JsonResponse({
                'success': True,
                'categories': categories,
                'audiences': audiences,
                'status_choices': status_choices
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)



#achievement
# Add these to your existing views.py

@login_required
@user_passes_test(is_admin)
def achievement_list(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Get filter parameters
            category = request.GET.get('category', '')
            date_from = request.GET.get('date_from', '')
            search = request.GET.get('search', '')
            page = request.GET.get('page', 1)
            show_deleted = request.GET.get('show_deleted', 'false') == 'true'
            
            # Start with base queryset
            if show_deleted:
                achievements = Achievement.all_objects.filter(is_active=False)
            else:
                achievements = Achievement.objects.filter(is_active=True)
            
            # Apply filters
            if category:
                achievements = achievements.filter(category_id=category)
            
            if date_from:
                achievements = achievements.filter(awarded_on__gte=date_from)
            
            if search:
                achievements = achievements.filter(
                    Q(title__icontains=search) |
                    Q(content__icontains=search) |
                    Q(context__icontains=search) |
                    Q(awarded_by__icontains=search)
                )
            
            # Pagination
            paginator = Paginator(achievements.order_by('-awarded_on'), 10)
            page_obj = paginator.get_page(page)
            
            # Prepare data for response
            achievements_data = []
            for achievement in page_obj:
                achievement_data = {
                    'id': achievement.id,
                    'title': achievement.title,
                    'heading': achievement.heading,
                    'context': achievement.context,
                    'content': achievement.content,
                    'team_name': achievement.team_name,
                    'person_in_charge': achievement.person_in_charge,
                    'location': achievement.location,
                    'awarded_on': achievement.awarded_on.strftime('%Y-%m-%d') if achievement.awarded_on else None,
                    'start_date': achievement.start_date.strftime('%Y-%m-%d') if achievement.start_date else None,
                    'end_date': achievement.end_date.strftime('%Y-%m-%d') if achievement.end_date else None,
                    'awarded_by': achievement.awarded_by,
                    'category': achievement.category.category,
                    'category_id': achievement.category.id,
                    'is_active': achievement.is_active,
                }
                
                # Get featured image if exists
                featured_image = achievement.images.filter(is_active=True).first()
                if featured_image:
                    achievement_data['featured_image'] = featured_image.image.url
                
                achievements_data.append(achievement_data)
            
            # Add categories to AJAX response
            categories = list(Category.objects.filter(is_active=True, scope_id__in=[3, 7]).values('id', 'category'))
            return JsonResponse({
                'success': True,
                'achievements': achievements_data,
                'categories': categories,
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            })
        except Exception as e:
            logger.error(f"Error loading achievements: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # For non-AJAX requests, return the template with categories for the filter dropdown
    categories = Category.objects.filter(is_active=True, scope_id__in=[3, 7])
    return render(request, 'admin/achievement/achievement_list.html', {
        'categories': categories
    })

@login_required
@user_passes_test(is_admin)
def achievement_form_data(request):
    try:
        categories = list(Category.objects.filter(is_active=True, scope_id__in=[3, 7]).values('id', 'category'))
        
        return JsonResponse({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        logger.error(f"Error loading achievement form data: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def achievement_create(request):
    if request.method == 'POST':
        try:
            form_data = request.POST.dict()
            files = request.FILES
            
            # Validate required fields
            required_fields = ['title']
            for field in required_fields:
                if not form_data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'error': f'{field} is required'
                    }, status=400)

            # Create the achievement
            achievement = Achievement.objects.create(
                title=form_data['title'],
                heading=form_data.get('heading', ''),
                context=form_data.get('context', ''),
                content=form_data.get('content', ''),
                team_name=form_data.get('team_name', ''),
                person_in_charge=form_data.get('person_in_charge', ''),
                location=form_data.get('location', ''),
                awarded_on=form_data.get('awarded_on'),
                start_date=form_data.get('start_date'),
                end_date=form_data.get('end_date'),
                awarded_by=form_data.get('awarded_by', ''),
                category_id=form_data.get('category'),
                admin=request.user.admin
            )

            # Handle images
            if 'images' in files:
                for image in files.getlist('images'):
                    AchievementImage.objects.create(achievement=achievement, image=image)

            return JsonResponse({
                'success': True,
                'message': 'Achievement created successfully'
            })
        except Exception as e:
            logger.error(f"Error creating achievement: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def achievement_update(request, pk):
    if request.method == 'POST':
        try:
            achievement = get_object_or_404(Achievement, pk=pk)
            form_data = request.POST.dict()
            files = request.FILES
            
            # Validate required fields
            required_fields = ['title', 'context', 'content', 'awarded_by', 'awarded_on', 'category']
            for field in required_fields:
                if not form_data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'error': f'{field} is required'
                    }, status=400)

            # Parse dates
            try:
                awarded_on = datetime.strptime(form_data['awarded_on'], '%Y-%m-%d').date() if form_data['awarded_on'] else None
                start_date = datetime.strptime(form_data['start_date'], '%Y-%m-%d').date() if form_data.get('start_date') else None
                end_date = datetime.strptime(form_data['end_date'], '%Y-%m-%d').date() if form_data.get('end_date') else None
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid date format (YYYY-MM-DD)'
                }, status=400)

            # Update fields
            achievement.title = form_data['title']
            achievement.heading = form_data.get('heading', '')
            achievement.context = form_data['context']
            achievement.content = form_data['content']
            achievement.awarded_by = form_data['awarded_by']
            achievement.team_name = form_data.get('team_name', '')
            achievement.person_in_charge = form_data.get('person_in_charge', '')
            achievement.location = form_data.get('location', '')
            achievement.awarded_on = awarded_on
            achievement.start_date = start_date
            achievement.end_date = end_date
            achievement.category_id = form_data['category']
            
            # Handle new images
            if 'images' in files:
                for image in files.getlist('images'):
                    AchievementImage.objects.create(achievement=achievement, image=image)

            achievement.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Achievement updated successfully'
            })
        except Exception as e:
            logger.error(f"Error updating achievement: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def achievement_delete(request, pk):
    if request.method == 'POST':
        try:
            achievement = get_object_or_404(Achievement, pk=pk, is_active=True)
            achievement.is_active = False
            achievement.save()
            return JsonResponse({
                'success': True, 
                'message': f'Achievement "{achievement.title}" has been moved to trash'
            })
        except Exception as e:
            logger.error(f"Error deleting achievement: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def achievement_image_delete(request, pk):
    if request.method == 'POST':
        try:
            image = get_object_or_404(AchievementImage, pk=pk)
            achievement_id = image.achievement.id
            image.delete()
            return JsonResponse({
                'success': True,
                'message': 'Image deleted successfully',
                'achievement_id': achievement_id
            })
        except Exception as e:
            logger.error(f"Error deleting achievement image: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

#accomplishment

@login_required
@user_passes_test(is_admin)
def accomplishment_list(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Get filter parameters
            category = request.GET.get('category', '')
            date_from = request.GET.get('date_from', '')
            search = request.GET.get('search', '')
            page = request.GET.get('page', 1)
            show_deleted = request.GET.get('show_deleted', 'false').lower() == 'true'
            
            # Start with base queryset
            if show_deleted:
                accomplishments = Accomplishment.all_objects.filter(is_active=False).select_related(
                    'category', 'admin__account'
                ).prefetch_related('images')
            else:
                accomplishments = Accomplishment.objects.filter(is_active=True).select_related(
                    'category', 'admin__account'
                ).prefetch_related('images')
            
            # Apply filters
            if category:
                accomplishments = accomplishments.filter(category_id=category)
            if date_from:
                accomplishments = accomplishments.filter(accomplish_on__gte=date_from)
            if search:
                accomplishments = accomplishments.filter(
                    Q(title__icontains=search) |
                    Q(context__icontains=search) |
                    Q(content__icontains=search) |
                    Q(impact__icontains=search)
                )
            
            # Pagination
            paginator = Paginator(accomplishments.order_by('-accomplish_on'), 10)
            page_obj = paginator.get_page(page)
            
            # Prepare data for response
            accomplishments_data = []
            for acc in page_obj:
                accomplishments_data.append({
                    'id': acc.id,
                    'title': acc.title,
                    'context': acc.context,
                    'content': acc.content,
                    'category': acc.category.category if acc.category else '',
                    'category_id': acc.category.id if acc.category else None,
                    'impact': acc.impact,
                    'recognition': acc.recognition,
                    'accomplish_on': acc.accomplish_on.strftime('%Y-%m-%d') if acc.accomplish_on else '',
                    'created_at': acc.created_at.strftime('%Y-%m-%d %H:%M'),
                    'updated_at': acc.updated_at.strftime('%Y-%m-%d %H:%M'),
                    'is_active': acc.is_active,
                    'featured_image': request.build_absolute_uri(acc.images.first().image.url) if acc.images.exists() else None,
                    'images': [
                        {
                            'id': img.id,
                            'url': request.build_absolute_uri(img.image.url),
                            'created_at': img.created_at.strftime('%Y-%m-%d %H:%M')
                        } for img in acc.images.all()
                    ]
                })
            
            # Get categories for filter dropdown (only scope_id 4 or 7)
            categories = Category.objects.filter(is_active=True, scope_id__in=[4, 7]).values('id', 'category')
            
            return JsonResponse({
                'success': True,
                'accomplishments': accomplishments_data,
                'categories': list(categories),
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def accomplishment_create(request):
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            
            # Validate required fields
            required_fields = ['title', 'context', 'content', 'category', 'accomplish_on']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'error': f'{field} is required'
                    }, status=400)

            # Create the accomplishment
            accomplishment = Accomplishment.objects.create(
                title=data['title'],
                context=data['context'],
                content=data['content'],
                category_id=data['category'],
                impact=data.get('impact', ''),
                recognition=data.get('recognition', ''),
                accomplish_on=data['accomplish_on'],
                admin=request.user.admin
            )

            # Handle images
            if 'images' in request.FILES:
                for image in request.FILES.getlist('images'):
                    AccomplishmentImage.objects.create(accomplishment=accomplishment, image=image)

            return JsonResponse({
                'success': True,
                'id': accomplishment.id,
                'message': 'Accomplishment created successfully'
            })

        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def accomplishment_update(request, pk):
    if request.method == 'POST':
        try:
            accomplishment = get_object_or_404(Accomplishment, pk=pk, is_active=True)
            data = request.POST.dict()

            # Update fields
            accomplishment.title = data.get('title', accomplishment.title)
            accomplishment.context = data.get('context', accomplishment.context)
            accomplishment.content = data.get('content', accomplishment.content)
            accomplishment.category_id = data.get('category', accomplishment.category_id)
            accomplishment.impact = data.get('impact', accomplishment.impact)
            accomplishment.recognition = data.get('recognition', accomplishment.recognition)
            
            if data.get('accomplish_on'):
                accomplishment.accomplish_on = data['accomplish_on']
            
            # Handle new images
            if 'images' in request.FILES:
                for image in request.FILES.getlist('images'):
                    AccomplishmentImage.objects.create(accomplishment=accomplishment, image=image)

            accomplishment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Accomplishment updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)

@login_required
@user_passes_test(is_admin)
def accomplishment_detail(request, pk):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            accomplishment = get_object_or_404(Accomplishment, pk=pk, is_active=True)
            
            # Get images
            images = []
            for img in accomplishment.images.all():
                images.append({
                    'id': img.id,
                    'url': request.build_absolute_uri(img.image.url),
                    'created_at': img.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            return JsonResponse({
                'success': True,
                'accomplishment': {
                    'id': accomplishment.id,
                    'title': accomplishment.title,
                    'context': accomplishment.context,
                    'content': accomplishment.content,
                    'category_id': accomplishment.category.id if accomplishment.category else None,
                    'category_name': accomplishment.category.category if accomplishment.category else '',
                    'impact': accomplishment.impact,
                    'recognition': accomplishment.recognition,
                    'accomplish_on': accomplishment.accomplish_on.strftime('%Y-%m-%d') if accomplishment.accomplish_on else None,
                    'created_at': accomplishment.created_at.strftime('%Y-%m-%d %H:%M'),
                    'updated_at': accomplishment.updated_at.strftime('%Y-%m-%d %H:%M'),
                    'images': images
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
@user_passes_test(is_admin)
def accomplishment_form_data(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Only include categories with scope_id 4 or 7
            categories = list(Category.objects.filter(is_active=True, scope_id__in=[4, 7]).values('id', 'category'))
            status_choices = list(Status.objects.filter(is_active=True).values('id', 'type'))
            
            return JsonResponse({
                'success': True,
                'categories': categories,
                'status_choices': status_choices
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def accomplishment_image_delete(request, pk):
    if request.method == 'POST':
        try:
            image = get_object_or_404(AccomplishmentImage, pk=pk)
            accomplishment_id = image.accomplishment.id
            image.delete()
            return JsonResponse({'success': True, 'message': 'Image deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def accomplishment_delete(request, pk):
    if request.method == 'POST':
        try:
            accomplishment = get_object_or_404(Accomplishment, pk=pk, is_active=True)
            accomplishment.is_active = False
            accomplishment.save()
            return JsonResponse({'success': True, 'message': 'Accomplishment deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

#account
# Account List View (AJAX)
@login_required
@user_passes_test(is_admin)
def account_list(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Get filter parameters
            account_type = request.GET.get('account_type', '')
            is_active = request.GET.get('is_active', '')
            search = request.GET.get('search', '')
            page = request.GET.get('page', 1)
            
            # Start with base queryset
            accounts = Account.objects.all()
            
            # Apply filters
            if account_type:
                accounts = accounts.filter(account_type=account_type)
            if is_active:
                accounts = accounts.filter(is_active=(is_active == 'true'))
            if search:
                accounts = accounts.filter(
                    Q(email__icontains=search) |
                    Q(firstname__icontains=search) |
                    Q(lastname__icontains=search)
                )
            
            # Pagination
            paginator = Paginator(accounts.order_by('-created_at'), 10)
            page_obj = paginator.get_page(page)
            
            # Prepare data for response
            accounts_data = []
            for account in page_obj:
                accounts_data.append({
                    'id': account.id,
                    'email': account.email,
                    'firstname': account.firstname,
                    'lastname': account.lastname,
                    'middlename': account.middlename,
                    'contact_number': account.contact_number,
                    'account_type': account.account_type,
                    'is_active': account.is_active,
                    'profile_img': request.build_absolute_uri(account.profile_img.url) if account.profile_img else None,
                    'created_at': account.created_at.strftime('%Y-%m-%d %H:%M'),
                    'last_login': account.last_login.strftime('%Y-%m-%d %H:%M') if account.last_login else None,
                })
            
            return JsonResponse({
                'success': True,
                'accounts': accounts_data,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
            })
        except Exception as e:
            logger.error(f"Error in account_list: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

# Account Create View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def account_create(request):
    if request.method == 'POST':
        try:
            # Get data from request
            data = request.POST.dict()
            
            # Validate required fields
            required_fields = ['email', 'firstname', 'lastname', 'account_type']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'error': f'{field} is required'
                    }, status=400)

            # Check if email already exists
            if Account.objects.filter(email=data['email']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Email already exists'
                }, status=400)

            # Create the account
            account = Account.objects.create_user(
                email=data['email'],
                password=data.get('password', 'defaultpassword'),  # In production, generate a random password
                firstname=data['firstname'],
                lastname=data['lastname'],
                middlename=data.get('middlename', ''),
                contact_number=data.get('contact_number', ''),
                account_type=data['account_type'],
                is_active=data.get('is_active', 'true') == 'true'
            )

            # Handle profile image
            if 'profile_img' in request.FILES:
                account.profile_img = request.FILES['profile_img']
                account.save()

            return JsonResponse({
                'success': True,
                'account_id': account.id,
                'message': 'Account created successfully'
            })

        except Exception as e:
            logger.error(f"Error creating account: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)

# Account Update View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def account_update(request, pk):
    if request.method == 'POST':
        try:
            account = get_object_or_404(Account, pk=pk, is_active=True)
            data = request.POST.dict()

            # Update fields
            account.firstname = data.get('firstname', account.firstname)
            account.lastname = data.get('lastname', account.lastname)
            account.middlename = data.get('middlename', account.middlename)
            account.contact_number = data.get('contact_number', account.contact_number)
            account.account_type = data.get('account_type', account.account_type)
            account.is_active = data.get('is_active', str(account.is_active)) == 'true'
            
            # Update password if provided
            if 'password' in data and data['password']:
                account.set_password(data['password'])
            
            # Handle profile image
            if 'profile_img' in request.FILES:
                account.profile_img = request.FILES['profile_img']

            account.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Account updated successfully'
            })
        except Exception as e:
            logger.error(f"Error updating account: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)

# Account Delete View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def account_delete(request, pk):
    if request.method == 'POST':
        try:
            account = get_object_or_404(Account, pk=pk, is_active=True)
            account.is_active = False  # Soft delete
            account.save()
            return JsonResponse({'success': True, 'message': 'Account deactivated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

# Account Detail View (AJAX)
@login_required
@user_passes_test(is_admin)
def account_detail(request, pk):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            account = get_object_or_404(Account, pk=pk, is_active=True)
            
            return JsonResponse({
                'success': True,
                'account': {
                    'id': account.id,
                    'email': account.email,
                    'firstname': account.firstname,
                    'lastname': account.lastname,
                    'middlename': account.middlename,
                    'contact_number': account.contact_number,
                    'account_type': account.account_type,
                    'is_active': account.is_active,
                    'profile_img': request.build_absolute_uri(account.profile_img.url) if account.profile_img else None,
                    'created_at': account.created_at.strftime('%Y-%m-%d %H:%M'),
                    'last_login': account.last_login.strftime('%Y-%m-%d %H:%M') if account.last_login else None,
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

# Account Form Data (for dropdowns)
@login_required
@user_passes_test(is_admin)
def account_form_data(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            account_types = [
                {'value': 'admin', 'label': 'Admin'},
                {'value': 'user', 'label': 'User'}
            ]
            
            return JsonResponse({
                'success': True,
                'account_types': account_types
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

#complaint

@login_required
@user_passes_test(is_admin)
def complaints_list(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Get filter parameters
            status = request.GET.get('status', '')
            complaint_type = request.GET.get('type', '')
            search = request.GET.get('search', '')
            page = request.GET.get('page', 1)
            show_deleted = request.GET.get('show_deleted', 'false') == 'true'
            
            # Start with base queryset
            if show_deleted:
                complaints = Complaint.all_objects.filter(is_active=False)
            else:
                complaints = Complaint.objects.filter(is_active=True)
            
            # Apply filters
            if status:
                complaints = complaints.filter(remarks=status)
            if complaint_type:
                complaints = complaints.filter(complaint_type_id=complaint_type)
            if search:
                complaints = complaints.filter(
                    Q(description__icontains=search) |
                    Q(other_info__icontains=search) |
                    Q(user__account__firstname__icontains=search) |
                    Q(user__account__lastname__icontains=search)
                )
            
            # Pagination
            paginator = Paginator(complaints.order_by('-created_at'), 10)
            page_obj = paginator.get_page(page)
            
            # Prepare data for response
            complaints_data = []
            for complaint in page_obj:
                complaints_data.append({
                    'id': complaint.id,
                    'user_name': f"{complaint.user.account.firstname} {complaint.user.account.lastname}",
                    'complaint_type': complaint.complaint_type.type,
                    'description': complaint.description,
                    'remarks': complaint.remarks,
                    'created_at': complaint.created_at.strftime('%Y-%m-%d %H:%M'),
                    'updated_at': complaint.updated_at.strftime('%Y-%m-%d %H:%M') if complaint.updated_at else None,
                    'image': request.build_absolute_uri(complaint.complain_img.url) if complaint.complain_img else None,
                    'is_active': complaint.is_active,
                    'remark_info': complaint.remark_info,
                })
            
            # Get types for filter dropdown
            complaint_types = ComplaintType.objects.filter(is_active=True).values('id', 'type')
            
            return JsonResponse({
                'success': True,
                'complaints': complaints_data,
                'types': list(complaint_types),
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
            })
        except Exception as e:
            logger.error(f"Error in complaints_list: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def complaint_detail(request, pk):
    if request.method == 'GET':
        try:
            complaint = get_object_or_404(Complaint, pk=pk)
            
            data = {
                'success': True,
                'complaint': {
                    'id': complaint.id,
                    'user_name': f"{complaint.user.account.firstname} {complaint.user.account.lastname}",
                    'user_email': complaint.user.account.email,
                    'complaint_type': complaint.complaint_type.type,
                    'complaint_type_id': complaint.complaint_type.id,
                    'description': complaint.description,
                    'other_info': complaint.other_info,
                    'remarks': complaint.remarks,
                    'remark_info': complaint.remark_info,
                    'created_at': complaint.created_at.strftime('%Y-%m-%d %H:%M'),
                    'updated_at': complaint.updated_at.strftime('%Y-%m-%d %H:%M') if complaint.updated_at else None,
                    'image': request.build_absolute_uri(complaint.complain_img.url) if complaint.complain_img else None,
                    'is_active': complaint.is_active,
                }
            }
            
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    elif request.method == 'POST':
        try:
            complaint = get_object_or_404(Complaint, pk=pk)
            data = json.loads(request.body)
            
            # Update remarks
            if 'remarks' in data:
                complaint.remarks = data['remarks']
                complaint.admin = request.user.admin
            
            if 'remark_info' in data:
                complaint.remark_info = data['remark_info']
            
            complaint.save()
            
            # Log the update
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='Complaint',
                record_id=complaint.id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return JsonResponse({'success': True, 'message': 'Complaint updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def delete_complaint(request, pk):
    if request.method == 'POST':
        try:
            complaint = get_object_or_404(Complaint, pk=pk)
            complaint.delete()  # Soft delete
            
            # Log the deletion
            AuditLog.objects.create(
                user=request.user,
                action='delete',
                model_name='Complaint',
                record_id=complaint.id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return JsonResponse({'success': True, 'message': 'Complaint deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def restore_complaint(request, pk):
    if request.method == 'POST':
        try:
            complaint = get_object_or_404(Complaint, pk=pk, is_active=False)
            complaint.is_active = True
            complaint.save()
            
            # Log the restoration
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='Complaint',
                record_id=complaint.id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return JsonResponse({'success': True, 'message': 'Complaint restored successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def accomplishment_restore(request, pk):
    if request.method == 'POST':
        try:
            accomplishment = get_object_or_404(Accomplishment.all_objects, pk=pk, is_active=False)
            accomplishment.is_active = True
            accomplishment.save()
            return JsonResponse({'success': True, 'message': 'Accomplishment restored successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

#client view
class ClientViews:
    
    
    @staticmethod
    def landing_page(request):
        today = date.today()
    
        # Get active posts (limit to 4) - Simplified query
        posts = Post.objects.filter(
            is_active=True,
            status__in=['active', 'scheduled']
        ).select_related('category', 'admin').prefetch_related('images').order_by('-created_at')[:4]

        # Get active achievements (limit to 2)
        achievements = Achievement.objects.filter(
            is_active=True
        ).select_related('category', 'admin').prefetch_related('images').order_by('-awarded_on')[:2]

        # Get upcoming events (limit to 4)
        events = Event.objects.filter(
            is_active=True,
            status__in=['active', 'scheduled'],
            date_event__gte=today
        ).select_related('admin').prefetch_related('audiences', 'labels', 'types').order_by('date_event')[:4]

        # Get active announcements (limit to 6)
        announcements = Announcement.objects.filter(
            is_active=True,
            status__in=['active', 'scheduled'],
            start_publish_on__lte=today,
            end_publish_on__gte=today
        ).select_related('category', 'admin').prefetch_related('audiences').order_by('-start_publish_on')[:6]

        context = {
            'posts': posts,
            'achievements': achievements,
            'events': events,
            'announcements': announcements,
        }

        return render(request, 'client/Lpage.html', context)
    @staticmethod
    def post_list(request):
        # Get all active posts ordered by publish date
        posts = Post.objects.filter(is_active=True).order_by('-start_publish_on')

        # Get all active categories for filtering
        categories = Category.objects.filter(is_active=True)

        # Filter by category if specified
        category_slug = request.GET.get('category')
        if category_slug:
            posts = posts.filter(category__category=category_slug)

        # Pagination
        paginator = Paginator(posts, 10)  # Show 10 posts per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'categories': categories,
            'selected_category': category_slug,
        }
        return render(request, 'client/posts/post_list.html', context)
    @staticmethod
    def post_detail(request, pk):
        # Get the post or return 404
        post = get_object_or_404(Post, pk=pk, is_active=True)

        # Get related images
        images = PostImage.objects.filter(post=post, is_active=True)

        # Get related posts (same category)
        related_posts = Post.objects.filter(
            category=post.category,
            is_active=True
        ).exclude(pk=pk).order_by('-start_publish_on')[:4]

        context = {
            'post': post,
            'images': images,
            'related_posts': related_posts,
        }
        return render(request, 'client/posts/posts_detail.html', context)

    @staticmethod
    def announcement_list(request):
        from django.db.models.functions import TruncMonth
        announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
        # Get unique months from created_at
        announcement_dates = (
            Announcement.objects.filter(is_active=True)
            .annotate(month=TruncMonth('created_at'))
            .values_list('month', flat=True)
            .distinct()
            .order_by('-month')
        )
        return render(request, 'client/announcements/announcement_list.html', {
            'announcements': announcements,
            'announcement_dates': announcement_dates,
        })
    @staticmethod
    def announcement_detail(request, pk):
        announcement = Announcement.objects.get(pk=pk, is_active=True)
        return render(request, 'client/announcements/announcement_detail.html', {'announcement': announcement})

    @staticmethod
    def event_list(request):
        # Get all active events (not soft deleted)
        events = Event.objects.filter(is_active=True)

        # Filter by status if provided
        status = request.GET.get('status')
        if status in ['active', 'expired', 'scheduled']:
            events = events.filter(status=status)

        # Filter by date range if provided
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            events = events.filter(date_event__range=[start_date, end_date])

        # Filter by label if provided
        label = request.GET.get('label')
        if label:
            events = events.filter(labels__type__icontains=label)

        # Filter by type if provided
        event_type = request.GET.get('type')
        if event_type:
            events = events.filter(types__type__icontains=event_type)

        # Filter by audience if provided
        audience = request.GET.get('audience')
        if audience:
            # Corrected this line - filter through the EventAudience relationship
            events = events.filter(eventaudience__audience__type__icontains=audience)

        # Filter by search query if provided
        search_query = request.GET.get('search')
        if search_query:
            events = events.filter(
                Q(name__icontains=search_query) |
                Q(context__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )

        # Order events by date (upcoming first)
        events = events.order_by('date_event', 'start_at')

        # Pagination
        paginator = Paginator(events, 9)  # Show 9 events per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Get all labels, types, and audiences for filters
        all_labels = EventLabel.objects.filter(is_active=True)
        all_types = EventType.objects.filter(is_active=True)
        all_audiences = Audience.objects.filter(is_active=True)  # Changed to use Audience model

        context = {
            'page_obj': page_obj,
            'all_labels': all_labels,
            'all_types': all_types,
            'all_audiences': all_audiences,
            'current_filters': {
                'status': status,
                'start_date': start_date,
                'end_date': end_date,
                'label': label,
                'type': event_type,
                'audience': audience,
                'search': search_query,
            }
        }

        return render(request, 'client/events/event_list.html', context)
    @staticmethod
    def event_detail(request, pk):
        event = Event.objects.get(pk=pk, is_active=True)
        related_events = Event.objects.filter(
            is_active=True,
            labels__in=event.labels.all()
        ).exclude(pk=pk).distinct()[:3]

        context = {
            'event': event,
            'related_events': related_events
        }
        return render(request, 'client/events/event_detail.html', context)
    @staticmethod
    def achievements_list(request):
        # Get search query and category filter
        search_query = request.GET.get('search', '')
        category_id = request.GET.get('category')
        
        # Base queryset
        achievements = Achievement.objects.all()
        
        # Apply search filter if query exists
        if search_query:
            achievements = achievements.filter(title__icontains=search_query)
        
        # Apply category filter if selected
        if category_id:
            achievements = achievements.filter(category_id=category_id)
        
        # Get categories with scope_id 3 or 7
        categories = Category.objects.filter(scope_id__in=[3, 7], is_active=True)
        
        # Order by awarded date
        achievements = achievements.order_by('-awarded_on')
        
        context = {
            'achievements': achievements,
            'categories': categories,
        }
        
        return render(request, 'client/achievements/list.html', context)
    @staticmethod
    def achievements_detail(request, pk):
        achievement = get_object_or_404(
            Achievement.objects.filter(is_active=True)
            .select_related('category')
            .prefetch_related('images'),
            pk=pk
        )
        context = {
            'achievement': achievement,
        }
        return render(request, 'client/achievements/detail.html', context)

    @staticmethod
    def officers_list(request):
        officer_members = OfficerMember.all_objects.select_related('officer', 'position', 'department')
        print("OfficerMember count:", officer_members.count())
        members_by_sy = {}
        for member in officer_members:
            sy_key = f"{member.start_term.year} - {member.end_term.year}"
            if sy_key not in members_by_sy:
                members_by_sy[sy_key] = []
            members_by_sy[sy_key].append(member)
        print("Grouped S.Y. keys:", members_by_sy.keys())
        return render(request, 'client/officers/list.html', {'members_by_sy': members_by_sy})
    @staticmethod
    def about_page(request):
        """About us page"""
        departments = Department.objects.filter(is_active=True)
        committees = Committee.objects.filter(is_active=True)
        faculties = Faculty.objects.filter(is_active=True)
        
        return render(request, 'client/about.html', {
            'departments': departments,
            'committees': committees,
            'faculties': faculties,
        })
    # views.py
    @staticmethod
    def faculty_list(request):
        # Get all active faculty members
        faculty_members = Faculty.objects.filter(is_active=True).select_related(
            'position', 'college', 'department'
        ).order_by('lastname', 'firstname')

        # Group faculty by department
        faculty_by_department = {}
        for faculty in faculty_members:
            dept_key = faculty.department.id
            if dept_key not in faculty_by_department:
                faculty_by_department[dept_key] = {
                    'department': faculty.department,
                    'college': faculty.college,
                    'members': []
                }
            faculty_by_department[dept_key]['members'].append(faculty)

        context = {
            'faculty_by_department': faculty_by_department,
        }
        return render(request, 'client/professors/list.html', context)
    @staticmethod
    def faculty_detail(request, faculty_id):
        faculty = Faculty.objects.select_related(
            'position', 'college', 'department'
        ).get(id=faculty_id, is_active=True)

        context = {
            'faculty': faculty,
        }
        return render(request, 'client/professors/detail.html', context)
    @staticmethod
    def officer_list(request):
        # Get all active officers
        officers = Officer.objects.filter(is_active=True).order_by('-start_in_sy')

        # Group officers by school year
        officers_by_sy = {}
        for officer in officers:
            sy_key = f"{officer.start_in_sy}-{officer.end_in_sy}"
            if sy_key not in officers_by_sy:
                officers_by_sy[sy_key] = {
                    'start_sy': officer.start_in_sy,
                    'end_sy': officer.end_in_sy,
                    'officers': []
                }
            officers_by_sy[sy_key]['officers'].append(officer)

        context = {
            'officers_by_sy': officers_by_sy,
        }
        return render(request, 'client/officers/list.html', context)
    @staticmethod
    def officer_detail(request, officer_id):
        officer = Officer.objects.get(id=officer_id, is_active=True)
        members = OfficerMember.objects.filter(officer=officer, is_active=True).select_related('position', 'department')

        context = {
            'officer': officer,
            'members': members,
        }
        return render(request, 'client/officers/detail.html', context)
    @staticmethod
    def committees_list(request):
        # Get all active committee members with related data
        committee_members = CommitteeMember.all_objects.select_related('committee')

        # Group members by committee
        members_by_committee = {}
        for member in committee_members:
            if member.committee.name not in members_by_committee:
                members_by_committee[member.committee.name] = []
            members_by_committee[member.committee.name].append(member)

        return render(request, 'client/committees/list.html', {'members_by_committee': members_by_committee})

    @staticmethod
    def committee_detail(request, committee_id):
        committee = Committee.objects.get(id=committee_id, is_active=True)
        members = CommitteeMember.objects.filter(committee=committee, is_active=True)

        context = {
            'committee': committee,
            'members': members,
        }
        return render(request, 'client/committees/detail.html', context)
    @staticmethod
    def accomplishments_list(request):
        selected_category = request.GET.get('category', '')
        accomplishments = Accomplishment.objects.filter(is_active=True)
        if selected_category:
            accomplishments = accomplishments.filter(category_id=selected_category)
        accomplishments = accomplishments.select_related('category').prefetch_related('images').order_by('-accomplish_on')
        categories = Category.objects.filter(is_active=True, scope_id__in=[4, 7])
        return render(request, 'client/accomplishment/list.html', {
            'accomplishments': accomplishments,
            'categories': categories,
            'selected_category': selected_category,
        })
    @staticmethod
    class TransparencyListView(ListView):
        model = Transparency
        template_name = 'client/transparency/list.html'
        context_object_name = 'transparency_list'
        paginate_by = 10
    
        def get_queryset(self):
            queryset = Transparency.objects.select_related('category', 'status', 'admin')
            
            # Filter by category if provided
            category = self.request.GET.get('category')
            if category:
                queryset = queryset.filter(category__category=category)
                
            # Filter by status if provided
            status = self.request.GET.get('status')
            if status:
                queryset = queryset.filter(status__type=status)
                
            return queryset.order_by('-date')
    
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            # Filter categories to only show those with scope_id 5 (transparency)
            context['categories'] = Category.objects.filter(scope_id=5)
            context['statuses'] = Status.objects.all()
            return context
    @staticmethod
    class TransparencyDetailView(DetailView):
        model = Transparency
        template_name = 'client/transparency/detail.html'
        context_object_name = 'transparency'

        def get_object(self):
            return get_object_or_404(
                Transparency.objects.select_related('category', 'status', 'admin'),
                pk=self.kwargs.get('pk')
            )
            
    @staticmethod
    def contact_page(request):
        """Contact us page"""
        return render(request, 'client/contact.html')
    @staticmethod
    def base(request):
        """Base template for the client"""
        return render(request, 'client/base.html')
    @staticmethod
    @login_required
    def feedback(request):
        if request.method == 'POST':
            rating = request.POST.get('rating')
            comment = request.POST.get('comment')
            feedback_type_id = request.POST.get('feedback_type')

            try:
                user = User.objects.get(account=request.user)
                Feedback.objects.create(
                    user=user,
                    rating=rating,
                    comment=comment,
                    feedback_type_id=feedback_type_id
                )
                # If AJAX, return JSON
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                # Otherwise, normal redirect
                messages.success(request, 'Thank you for your feedback!')
                return redirect('landing_page')
            except User.DoesNotExist:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'User profile not found.'}, status=400)
                messages.error(request, 'User profile not found.')
                return redirect('feedback')

        feedback_types = FeedbackType.objects.all()
        return render(request, 'client/client_inputs/feedback.html', {'feedback_types': feedback_types})

    @staticmethod
    @login_required
    def complaint(request):
        if request.method == 'POST':
            complaint_type_id = request.POST.get('complaint_type')
            description = request.POST.get('description')
            complain_img = request.FILES.get('complain_img')

            try:
                user = User.objects.get(account=request.user)
                complaint = Complaint.objects.create(
                    user=user,
                    complaint_type_id=complaint_type_id,
                    description=description,
                    complain_img=complain_img
                )
                
                # If AJAX, return JSON
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                
                # Otherwise, normal redirect
                messages.success(request, 'Your complaint has been submitted successfully!')
                return redirect('landing_page')
                
            except User.DoesNotExist:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'User profile not found.'}, status=400)
                messages.error(request, 'User profile not found.')
                return redirect('auth')
            except Exception as e:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
                messages.error(request, f'Error submitting complaint: {str(e)}')
                return redirect('complaint')

        # GET request - show the form
        complaint_types = ComplaintType.objects.filter(is_active=True)
        return render(request, 'client/client_inputs/complaint.html', {'complaint_types': complaint_types})
    @staticmethod
    @login_required
    def profile(request):
        user = request.user
        # Get the 'from' parameter or fallback to home
        from_url = request.GET.get('from') or request.session.get('profile_from') or '/'
        if request.method == 'POST':
            # After POST, keep the original 'from' in session
            request.session['profile_from'] = from_url
            # Check if password change is requested
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if current_password or new_password or confirm_password:
                # Password change logic
                if not (current_password and new_password and confirm_password):
                    messages.error(request, 'Please fill in all password fields.')
                elif not user.check_password(current_password):
                    messages.error(request, 'Current password is incorrect.')
                elif new_password != confirm_password:
                    messages.error(request, 'New passwords do not match.')
                elif len(new_password) < 8:
                    messages.error(request, 'New password must be at least 8 characters.')
                else:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Password changed successfully!')
                    login(request, user)
                return redirect('profile')

            # Only update profile if the email is present in POST (i.e., profile form was submitted)
            if request.POST.get('email'):
                user.firstname = request.POST.get('firstname', user.firstname)
                user.lastname = request.POST.get('lastname', user.lastname)
                user.middlename = request.POST.get('middlename', user.middlename)
                user.email = request.POST.get('email', user.email)
                user.contact_number = request.POST.get('contact_number', user.contact_number)

                # Only update the image if a new one is uploaded
                if request.FILES.get('profile_img'):
                    user.profile_img = request.FILES['profile_img']

                try:
                    user.save()
                    messages.success(request, 'Profile updated successfully!')
                except Exception as e:
                    messages.error(request, f'Error updating profile: {str(e)}')

                return redirect('profile')

        # On GET, store the 'from' parameter in session
        if 'from' in request.GET:
            request.session['profile_from'] = from_url
        return render(request, 'client/client_inputs/profile.html', {'from_url': from_url})

# Create an instance to use in urls.py
client_views = ClientViews()

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def export_data(request):
    model_name = request.GET.get('model')
    export_format = request.GET.get('format', 'excel')
    # Map model names to Django models and visible fields
    model_map = {
        'accomplishment': (Accomplishment, ['title', 'category', 'context', 'content', 'impact', 'recognition', 'accomplish_on']),
        'post': (Post, ['title', 'category', 'context', 'content', 'created_at', 'start_publish_on', 'end_publish_on', 'status']),
        'achievement': (Achievement, ['title', 'category', 'context', 'content', 'awarded_by', 'awarded_on']),
        'announcement': (Announcement, ['title', 'category', 'context', 'content', 'created_at', 'start_publish_on', 'end_publish_on', 'status', 'landmark', 'location', 'date_post', 'time_post']),
        'event': (Event, ['name', 'category', 'context', 'content', 'created_at', 'date_event', 'start_at', 'end_at', 'status']),
        
        # Add more as needed
    }
    if model_name not in model_map:
        return HttpResponse('Invalid model', status=400)
    model, fields = model_map[model_name]
    queryset = model.objects.filter(is_active=True)
    # Filtering (optional, e.g., by category)
    category = request.GET.get('category')
    if category and hasattr(model, 'category_id'):
        queryset = queryset.filter(category_id=category)
    # Prepare data
    data = []
    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field, '')
            if hasattr(value, 'category'):
                value = value.category
            elif hasattr(value, 'strftime'):
                value = value.strftime('%Y-%m-%d')
            row.append(str(value))
        data.append(row)
    # Excel export
    if export_format == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append([f.replace('_', ' ').title() for f in fields])
        for row in data:
            ws.append(row)
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={model_name}_export.xlsx'
        return response
    # PDF export
    elif export_format == 'pdf' and WEASYPRINT_AVAILABLE:
        html_string = render_to_string('admin/export_table.html', {'fields': fields, 'data': data, 'model_name': model_name.title()})
        pdf_file = BytesIO()
        HTML(string=html_string).write_pdf(pdf_file)
        pdf_file.seek(0)
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={model_name}_export.pdf'
        return response
    else:
        return HttpResponse('Export format not supported or PDF library not installed.', status=400)

@login_required
@user_passes_test(is_admin)
def achievement_detail_admin(request, pk):
    try:
        achievement = get_object_or_404(Achievement, pk=pk)
        images = [
            {
                'id': img.id,
                'url': request.build_absolute_uri(img.image.url)
            } for img in achievement.images.all()
        ]
        data = {
            'id': achievement.id,
            'title': achievement.title,
            'heading': achievement.heading,
            'context': achievement.context,
            'content': achievement.content,
            'team_name': achievement.team_name,
            'person_in_charge': achievement.person_in_charge,
            'location': achievement.location,
            'awarded_on': achievement.awarded_on.strftime('%Y-%m-%d') if achievement.awarded_on else '',
            'start_date': achievement.start_date.strftime('%Y-%m-%d') if achievement.start_date else '',
            'end_date': achievement.end_date.strftime('%Y-%m-%d') if achievement.end_date else '',
            'awarded_by': achievement.awarded_by,
            'category_id': achievement.category_id,
            'images': images
        }
        return JsonResponse({'success': True, 'achievement': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def achievement_restore(request, pk):
    if request.method == 'POST':
        try:
            achievement = get_object_or_404(Achievement.all_objects, pk=pk, is_active=False)
            achievement.is_active = True
            achievement.save()
            return JsonResponse({'success': True, 'message': 'Achievement restored successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

# Announcement Form View (for modal)
@login_required
@user_passes_test(is_admin)
def announcement_form(request, pk=None):
    audiences = Audience.objects.all()
    selected_audiences = []
    if pk:
        announcement = Announcement.objects.get(pk=pk)
        selected_audiences = list(announcement.audiences.values_list('id', flat=True))
    return render(request, 'admin/announcement/announcement_form.html', {
        'audiences': audiences,
        'selected_audiences': selected_audiences
    })

@login_required
@user_passes_test(is_admin)
def event_form(request, pk=None):
    event_labels = EventLabel.objects.filter(is_active=True)
    event_types = EventType.objects.filter(is_active=True)
    audiences = Audience.objects.filter(is_active=True)
    selected_labels = []
    selected_types = []
    selected_audiences = []
    if pk:
        event = Event.objects.get(pk=pk)
        selected_labels = list(event.labels.values_list('id', flat=True))
        selected_types = list(event.types.values_list('id', flat=True))
        selected_audiences = list(event.audiences.values_list('id', flat=True))
    return render(request, 'admin/event/event_form.html', {
        'event_labels': event_labels,
        'event_types': event_types,
        'audiences': audiences,
        'selected_labels': selected_labels,
        'selected_types': selected_types,
        'selected_audiences': selected_audiences,
    })

@login_required
@user_passes_test(is_admin)
def event_categories_api(request):
    labels = list(EventLabel.objects.filter(is_active=True).values('id', 'type', 'description'))
    types = list(EventType.objects.filter(is_active=True).values('id', 'type', 'description'))
    audiences = list(Audience.objects.filter(is_active=True).values('id', 'type', 'description'))
    return JsonResponse({
        'success': True,
        'labels': [{'id': l['id'], 'name': l['type'], 'description': l['description']} for l in labels],
        'types': [{'id': t['id'], 'name': t['type'], 'description': t['description']} for t in types],
        'audiences': [{'id': a['id'], 'name': a['type'], 'description': a['description']} for a in audiences],
    })

# Transparency views
@login_required
@user_passes_test(is_admin)
def transparency_list(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Get filter parameters
        status = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        search = request.GET.get('search', '')
        page = request.GET.get('page', 1)
        show_deleted = request.GET.get('show_deleted', 'false') == 'true'

        # Base queryset
        queryset = Transparency.objects.all()

        # Apply filters
        if show_deleted:
            queryset = queryset.filter(is_active=False)
        else:
            queryset = queryset.filter(is_active=True)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(start_publish_on__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(end_publish_on__lte=date_to)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # Pagination
        paginator = Paginator(queryset, 10)
        try:
            transparency = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            transparency = paginator.page(1)

        # Prepare response data
        data = {
            'transparency_list': [
                {
                    'id': t.id,
                    'title': t.title,
                    'description': t.description,
                    'date': t.date.strftime('%Y-%m-%d') if t.date else None,
                    'status': t.status.type if hasattr(t.status, 'type') else str(t.status),
                    'document': t.document.url if t.document else None,
                    'is_active': t.is_active,
                    # Add more fields as needed
                }
                for t in transparency
            ],
            'total_pages': paginator.num_pages,
            'current_page': transparency.number,
            'has_next': transparency.has_next(),
            'has_previous': transparency.has_previous(),
            'next_page_number': transparency.next_page_number() if transparency.has_next() else None,
            'previous_page_number': transparency.previous_page_number() if transparency.has_previous() else None,
            'start_index': transparency.start_index(),
            'end_index': transparency.end_index(),
            'paginator': {
                'count': paginator.count,
                'num_pages': paginator.num_pages
            }
        }

        return JsonResponse(data)

    return render(request, 'admin/transparency/transparency_list.html')

@login_required
@user_passes_test(is_admin)
def transparency_form(request):
    return render(request, 'admin/transparency/transparency_form.html')

@login_required
@user_passes_test(is_admin)
def create_transparency(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            context = request.POST.get('context')
            description = request.POST.get('description')
            date = request.POST.get('date')
            document_url = request.POST.get('document_url')
            status_value = request.POST.get('status')
            from .models import Status
            status_obj = None
            if status_value:
                try:
                    status_obj = Status.objects.get(type=status_value)
                except Status.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'Status "{status_value}" does not exist.'})
            document = request.FILES.get('document')
            transparency = Transparency.objects.create(
                title=title,
                context=context,
                description=description,
                date=date,
                document_url=document_url,
                status=status_obj,
                admin=request.user.admin,
                document=document  # This line is correct if 'document' is not None
            )
            if 'document' in request.FILES:
                transparency.document = request.FILES['document']
            transparency.save()
            return JsonResponse({
                'success': True,
                'message': 'Document created successfully',
                'transparency': {
                    'id': transparency.id,
                    'title': transparency.title,
                    'context': transparency.context,
                    'description': transparency.description,
                    'date': transparency.date.strftime('%Y-%m-%d') if transparency.date else None,
                    'document_url': transparency.document_url,
                    'status': transparency.status.type if hasattr(transparency.status, 'type') else str(transparency.status),
                    'is_active': transparency.is_active,
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin)
def update_transparency(request, transparency_id):
    if request.method == 'GET':
        try:
            transparency = Transparency.objects.get(id=transparency_id)
            return JsonResponse({
                'success': True,
                'transparency': {
                    'id': transparency.id,
                    'title': transparency.title,
                    'context': transparency.context,
                    'description': transparency.description,
                    'date': transparency.date.strftime('%Y-%m-%d') if transparency.date else None,
                    'document': transparency.document.url if transparency.document else None,
                    'status': transparency.status.type if hasattr(transparency.status, 'type') else str(transparency.status),
                    'is_active': transparency.is_active,
                }
            })
        except Transparency.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Document not found'
            })

    elif request.method == 'POST':
        try:
            transparency = Transparency.objects.get(id=transparency_id)
            transparency.title = request.POST.get('title')
            transparency.context = request.POST.get('context')
            transparency.description = request.POST.get('description')
            transparency.date = request.POST.get('date')
            transparency.document_url = request.POST.get('document_url')
            status_value = request.POST.get('status')
            from .models import Status
            if status_value:
                try:
                    transparency.status = Status.objects.get(type=status_value)
                except Status.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'Status "{status_value}" does not exist.'})
            transparency.save()
            if 'document' in request.FILES:
                transparency.document = request.FILES['document']
            transparency.save()
            return JsonResponse({
                'success': True,
                'message': 'Document updated successfully'
            })
        except Transparency.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Document not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin)
def delete_transparency(request, transparency_id):
    if request.method == 'POST':
        try:
            transparency = Transparency.objects.get(id=transparency_id)
            transparency.is_deleted = True
            transparency.save()
            return JsonResponse({
                'success': True,
                'message': 'Document deleted successfully'
            })
        except Transparency.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Document not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin)
def restore_transparency(request, transparency_id):
    if request.method == 'POST':
        try:
            transparency = Transparency.objects.get(id=transparency_id)
            transparency.is_deleted = False
            transparency.save()
            return JsonResponse({
                'success': True,
                'message': 'Document restored successfully'
            })
        except Transparency.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Document not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def account_restore(request, pk):
    if request.method == 'POST':
        try:
            account = get_object_or_404(Account, pk=pk, is_active=False)
            account.is_active = True
            account.save()
            return JsonResponse({'success': True, 'message': 'Account restored successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

