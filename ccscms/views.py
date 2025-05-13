from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
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


logger = logging.getLogger(__name__)

from .models import (
    Account, User, Admin, Post, Event, Announcement, Complaint, Feedback,
    Achievement, Accomplishment, AuditLog, Volunteer, Officer, OfficerMember,
    EventLabel, EventType, EventLabelList, EventTypeList, EventAudience, Audience,
    Status, Category, College, Department, Position, Committee, CommitteeMember,
    Faculty, ComplaintType, Transparency, GalleryPost, GalleryPostImage,
    PostImage, AccomplishmentImage, AchievementImage, AnnouncementAudience, 
    
)

def is_admin(user):
    """Check if user is an admin"""
    return hasattr(user, 'admin')

class AuthView(View):
    template_name = 'auth/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            if is_admin(request.user):
                return redirect('admin_dashboard')
            return redirect('landing_page')
        return render(request, self.template_name)
    
    @method_decorator(csrf_protect)
    def post(self, request):
        if 'login' in request.POST:
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                if is_admin(user):
                    return redirect('admin_dashboard')
                return redirect('landing_page')
            messages.error(request, 'Invalid email or password.')
            return redirect('auth')
        
        elif 'signup' in request.POST:
            email = request.POST.get('email')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            contact_number = request.POST.get('contact_number')
            
            if password != password2:
                messages.error(request, 'Passwords do not match.')
                return redirect('auth')
            
            if Account.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('auth')
            
            try:
                user = Account.objects.create_user(
                    email=email,
                    password=password,
                    firstname=firstname,
                    lastname=lastname,
                    contact_number=contact_number,
                    account_type='user'
                )
                
                # Generate a unique student number (using timestamp to ensure uniqueness)
                username = email.split('@')[0]
                student_number = f"ST{timezone.now().strftime('%Y%m%d%H%M%S')}"
                
                User.objects.create(
                    account=user,
                    username=username,
                    student_number=student_number,
                    COR_img=None
                )
                
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('auth')
            
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                return redirect('auth')
        
        return redirect('auth')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
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
                    'categories': Category.objects.filter(is_active=True)
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
        }
    except Exception as e:
        logger.error(f"Error in get_dashboard_data: {e}", exc_info=True)
        raise


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
            
        search = request.GET.get('search')
        if search:
            events = events.filter(
                Q(name__icontains=search) |
                Q(location__icontains=search) |
                Q(description__icontains=search)
            )
            
        paginator = Paginator(events.order_by('-date_event'), 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        events_data = []
        for event in page_obj:
            event_data = {
                'id': event.id,
                'name': event.name,
                'description': event.description,
                'context': event.context,
                'date_event': event.date_event.strftime("%Y-%m-%d") if event.date_event else None,
                'start_at': event.start_at.strftime("%H:%M") if event.start_at else None,
                'end_at': event.end_at.strftime("%H:%M") if event.end_at else None,
                'location': event.location,
                'status': event.status,
                'event_img': request.build_absolute_uri(event.event_img.url) if event.event_img else None,                'is_active': event.is_active
            }
            events_data.append(event_data)
            
        return JsonResponse({
            'events': events_data,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
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
                'eventStatus': 'status',
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
                if form_field in ['eventName', 'eventStatus', 'eventDate', 
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
                    'featured_image': request.build_absolute_uri(event.event_img.url) if event.event_img else None,
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
    event_labels = list(EventLabel.objects.filter(is_active=True).values('id', 'type'))
    event_types = list(EventType.objects.filter(is_active=True).values('id', 'type'))
    audiences = list(Audience.objects.filter(is_active=True).values('id', 'type'))
    
    return JsonResponse({
        'success': True,
        'event_labels': event_labels,
        'event_types': event_types,
        'audiences': audiences,
    })
    
    # Add these views to your existing views.py

class EventRestoreView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_admin(self.request.user)

    def post(self, request, pk):
        try:
            event = get_object_or_404(Event, pk=pk, is_active=False)
            event.is_active = True  # Change to True to restore the event
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
        else:
            return JsonResponse({'success': False, 'error': 'Invalid category type'}, status=400)
            
        return JsonResponse({
            'success': True,
            'id': obj.id,
            'type': obj.type,
            'description': obj.description,
            'is_active': obj.is_active
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

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
        
        if category_type == 'label':
            obj = get_object_or_404(EventLabel, pk=item_id)
        elif category_type == 'type':
            obj = get_object_or_404(EventType, pk=item_id)
        elif category_type == 'audience':
            obj = get_object_or_404(Audience, pk=item_id)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid category type'}, status=400)
            
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
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

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
            categories = list(Category.objects.filter(is_active=True).values('id', 'category'))
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
                    'is_active': announcement.is_active
                })
            
            # Get categories for filter dropdown
            categories = list(Category.objects.filter(is_active=True).values('id', 'category'))
            
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
            })
        except Exception as e:
            logger.error(f"Error in announcement_list: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

# Announcement Create View (AJAX)
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def announcement_create(request):
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            
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

            start_publish = parse_date(data.get('start_publish_on'))
            end_publish = parse_date(data.get('end_publish_on'))

            # Create the announcement
            announcement = Announcement.objects.create(
                title=data['title'],
                content=data['content'],
                context=data['context'],
                category_id=data['category'],
                status=data.get('status', 'draft'),
                admin=request.user.admin,
                start_publish_on=start_publish,  # Can be None
                end_publish_on=end_publish       # Can be None
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
            announcement.title = data.get('title', announcement.title)
            announcement.content = data.get('content', announcement.content)
            announcement.context = data.get('context', announcement.context)
            announcement.category_id = data.get('category', announcement.category_id)
            announcement.status = data.get('status', announcement.status)
            announcement.start_publish_on = start_publish
            announcement.end_publish_on = end_publish
            
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
            announcement = get_object_or_404(Announcement, pk=pk, is_active=False)
            announcement.is_active = True
            announcement.save()
            return JsonResponse({'success': True, 'message': 'Announcement restored successfully'})
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
            categories = list(Category.objects.filter(is_active=True).values('id', 'category'))
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
            status = request.GET.get('status', '')
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
            if status:
                if status == 'active':
                    achievements = achievements.filter(is_active=True)
                elif status == 'inactive':
                    achievements = achievements.filter(is_active=False)
            
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
                achievements_data.append({
                    'id': achievement.id,
                    'title': achievement.title,
                    'context': achievement.context,
                    'content': achievement.content,
                    'awarded_by': achievement.awarded_by,
                    'awarded_on': achievement.awarded_on.strftime('%Y-%m-%d') if achievement.awarded_on else '',
                    'category': achievement.category.category if achievement.category else '',
                    'is_active': achievement.is_active,
                    'featured_image': request.build_absolute_uri(achievement.images.first().image.url) if achievement.images.exists() else None,
                    'images': [
                        {'id': img.id, 'url': request.build_absolute_uri(img.image.url)}
                        for img in achievement.images.all()
                    ]
                })
            
            return JsonResponse({
                'success': True,
                'achievements': achievements_data,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count
            })
        except Exception as e:
            logger.error(f"Error loading achievement list: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # For non-AJAX requests, return the template with categories for the filter dropdown
    categories = Category.objects.filter(is_active=True)
    return render(request, 'admin/achievement/achievement_list.html', {
        'categories': categories
    })

@login_required
@user_passes_test(is_admin)
def achievement_form_data(request):
    try:
        categories = list(Category.objects.filter(is_active=True).values('id', 'category'))
        statuses = list(Status.objects.filter(is_active=True).values('id', 'type'))
        
        # Create a default status if none exists
        if not statuses:
            default_status = Status.objects.create(
                type='active',
                description='Default status'
            )
            statuses = [{'id': default_status.id, 'type': default_status.type}]
        
        return JsonResponse({
            'success': True,
            'categories': categories,
            'statuses': statuses
        })
    except Exception as e:
        logger.error(f"Error loading achievement form data: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# In your views.py, update the achievement views:

@login_required
@user_passes_test(is_admin)
def achievement_detail(request, pk):
    try:
        achievement = Achievement.objects.get(pk=pk)
        
        images = []
        for img in achievement.images.all():
            images.append({
                'id': img.id,
                'url': request.build_absolute_uri(img.image.url)
            })
        
        return JsonResponse({
            'success': True,
            'achievement': {
                'id': achievement.id,
                'title': achievement.title,
                'context': achievement.context,
                'content': achievement.content,
                'awarded_by': achievement.awarded_by,
                'team_name': achievement.team_name,
                'mentor': achievement.mentor,
                'location': achievement.location,
                'awarded_on': achievement.awarded_on.strftime('%Y-%m-%d') if achievement.awarded_on else None,
                'start_date': achievement.start_date.strftime('%Y-%m-%d') if achievement.start_date else None,
                'end_date': achievement.end_date.strftime('%Y-%m-%d') if achievement.end_date else None,
                'category_id': achievement.category.id if achievement.category else None,
                'category': achievement.category.category if achievement.category else '',
                'is_active': achievement.is_active,
                'featured_image': request.build_absolute_uri(achievement.images.first().image.url) if achievement.images.exists() else None,
                'images': images
            }
        })
    except Achievement.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Achievement not found'}, status=404)
    except Exception as e:
        logger.error(f"Error loading achievement detail: {str(e)}", exc_info=True)
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
            required_fields = ['title', 'status']
            for field in required_fields:
                if not form_data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'error': f'{field} is required'
                    }, status=400)

            # Get or create a default status if none exists
            try:
                status = Status.objects.get(pk=form_data['status'])
            except Status.DoesNotExist:
                # Create a default status if it doesn't exist
                status = Status.objects.create(
                    type='active',
                    description='Default active status'
                )

            # Create the achievement
            achievement = Achievement.objects.create(
                title=form_data['title'],
                context=form_data.get('context', ''),
                content=form_data.get('content', ''),
                team_name=form_data.get('team_name', ''),
                mentor=form_data.get('mentor', ''),
                location=form_data.get('location', ''),
                awarded_on=form_data.get('awarded_on'),
                start_date=form_data.get('start_date'),
                end_date=form_data.get('end_date'),
                awarded_by=form_data.get('awarded_by', ''),
                status=status,
                category_id=form_data.get('category'),
                admin=request.user.admin
            )

            # Handle images
            if 'images' in files:
                for image in files.getlist('images'):
                    AchievementImage.objects.create(achievement=achievement, image=image)

            return JsonResponse({
                'success': True,
                'id': achievement.id,
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
            achievement.context = form_data['context']
            achievement.content = form_data['content']
            achievement.awarded_by = form_data['awarded_by']
            achievement.team_name = form_data.get('team_name', '')
            achievement.mentor = form_data.get('mentor', '')
            achievement.location = form_data.get('location', '')
            achievement.awarded_on = awarded_on
            achievement.start_date = start_date
            achievement.end_date = end_date
            achievement.category_id = form_data['category']
            achievement.is_active = form_data.get('status', 'active') == 'active'
            
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
            achievement.delete()  # Soft delete
            return JsonResponse({'success': True, 'message': 'Achievement deleted successfully'})
        except Exception as e:
            logger.error(f"Error deleting achievement: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

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
            status = request.GET.get('status', '')
            category = request.GET.get('category', '')
            date_from = request.GET.get('date_from', '')
            search = request.GET.get('search', '')
            page = request.GET.get('page', 1)
            
            # Start with base queryset
            accomplishments = Accomplishment.objects.filter(is_active=True).select_related(
                'category', 'status', 'admin__account'
            ).prefetch_related('images')
            
            # Apply filters
            if status:
                accomplishments = accomplishments.filter(status__type=status)
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
                    'status': acc.status.type if acc.status else '',
                    'status_id': acc.status.id if acc.status else None,
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
            
            # Get categories for filter dropdown
            categories = Category.objects.filter(is_active=True).values('id', 'category')
            
            return JsonResponse({
                'success': True,
                'accomplishments': accomplishments_data,
                'categories': list(categories),
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count
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
            required_fields = ['title', 'context', 'content', 'category', 'status', 'accomplish_on']
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
                status_id=data['status'],
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
            accomplishment.status_id = data.get('status', accomplishment.status_id)
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

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def accomplishment_delete(request, pk):
    if request.method == 'POST':
        try:
            accomplishment = get_object_or_404(Accomplishment, pk=pk, is_active=True)
            accomplishment.delete()  # Soft delete
            return JsonResponse({'success': True, 'message': 'Accomplishment deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

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
                    'status_id': accomplishment.status.id if accomplishment.status else None,
                    'status_name': accomplishment.status.type if accomplishment.status else '',
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
            categories = list(Category.objects.filter(is_active=True).values('id', 'category'))
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
            accounts = Account.objects.filter(is_active=True)
            
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
            account.delete()  # Soft delete
            return JsonResponse({'success': True, 'message': 'Account deleted successfully'})
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
#client view
class ClientViews:
    
    
    @staticmethod
    def landing_page(request):
        today = date.today()
    
        # Get active posts (limit to 4)
        posts = Post.objects.filter(
            Q(status='active') | Q(status='scheduled'),
            start_publish_on__lte=today,
            end_publish_on__gte=today,
            is_active=True
        ).select_related('category', 'admin').prefetch_related('images')[:4]

        # Get active achievements (limit to 2)
        achievements = Achievement.objects.filter(
            is_active=True
        ).select_related('category', 'status', 'admin').prefetch_related('images')[:2]

        # Get upcoming events (limit to 4)
        events = Event.objects.filter(
            Q(status='active') | Q(status='scheduled'),
            date_event__gte=today,
            is_active=True
        ).select_related('admin').prefetch_related('audiences', 'labels', 'types')[:4]

        # Get active announcements (limit to 3)
        announcements = Announcement.objects.filter(
            Q(status='active') | Q(status='scheduled'),
            start_publish_on__lte=today,
            end_publish_on__gte=today,
            is_active=True
        ).select_related('category', 'admin').prefetch_related('audiences')[:3]

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
        announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
        return render(request, 'client/announcements/announcement_list.html', {'announcements': announcements})
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
        # Get all active achievements with related data
        achievements = Achievement.objects.filter(is_active=True)\
            .select_related('category', 'status')\
            .prefetch_related('images')\
            .order_by('-awarded_on')

        # Get filter options
        categories = Category.objects.filter(is_active=True)
        statuses = Status.objects.filter(is_active=True)

        context = {
            'achievements': achievements,
            'categories': categories,
            'statuses': statuses,
        }
        return render(request, 'client/achievements/list.html', context)
    @staticmethod
    def achievements_detail(request, pk):
        achievement = get_object_or_404(
            Achievement.objects.filter(is_active=True)
            .select_related('category', 'status')
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
    def contact_page(request):
        """Contact us page"""
        return render(request, 'client/contact.html')
    @staticmethod
    def base(request):
        """Base template for the client"""
        return render(request, 'client/base.html')
    
# Create an instance to use in urls.py
client_views = ClientViews()