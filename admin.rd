from ccscms.models import Account, Admin

admin = Account.objects.create_superuser(
    email='admin@gmail.com',
    password='admin1234',
    firstname='Admin',
    lastname='User',
    contact_number='+1234567890',
    account_type='admin'
)

Admin.objects.create(
    account=admin,
    adminname='superadmin',
    admin_type='head-admin'
)