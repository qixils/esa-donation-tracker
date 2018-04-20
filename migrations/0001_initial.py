# Generated by Django 2.0.4 on 2018-04-20 00:04

from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import mptt.fields
import timezone_field.fields
import tracker.models.event
import tracker.models.fields
import tracker.util
import tracker.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('post_office', '0006_attachment_mimetype'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('state', models.CharField(choices=[('PENDING', 'Pending'), ('DENIED', 'Denied'), ('HIDDEN', 'Hidden'), ('OPENED', 'Opened'), ('CLOSED', 'Closed')], default='OPENED', max_length=32)),
                ('description', models.TextField(blank=True, max_length=1024)),
                ('shortdescription', models.TextField(blank=True, help_text='Alternative description text to display in tight spaces', max_length=256, verbose_name='Short Description')),
                ('goal', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=20, null=True)),
                ('istarget', models.BooleanField(default=False, help_text="Set this if this bid is a 'target' for donations (bottom level choice or challenge)", verbose_name='Target')),
                ('allowuseroptions', models.BooleanField(default=False, help_text='If set, this will allow donors to specify their own options on the donate page (pending moderator approval)', verbose_name='Allow User Options')),
                ('revealedtime', models.DateTimeField(blank=True, null=True, verbose_name='Revealed Time')),
                ('total', models.DecimalField(decimal_places=2, default=Decimal('0.00'), editable=False, max_digits=20)),
                ('count', models.IntegerField(editable=False)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('biddependency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='dependent_bids', to='tracker.Bid', verbose_name='Dependency')),
            ],
            options={
                'ordering': ['event__date', 'speedrun__starttime', 'parent__name', 'name'],
                'permissions': (('top_level_bid', 'Can create new top level bids'), ('delete_all_bids', 'Can delete bids with donations attached'), ('view_hidden', 'Can view hidden bids')),
            },
        ),
        migrations.CreateModel(
            name='BidSuggestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='Name')),
                ('bid', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='suggestions', to='tracker.Bid')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Official ISO 3166 name for the country', max_length=64, unique=True)),
                ('alpha2', models.CharField(help_text='ISO 3166-1 Two-letter code', max_length=2, unique=True, validators=[django.core.validators.RegexValidator(message='Country Alpha-2 code must be exactly 2 uppercase alphabetic characters', regex='^[A-Z]{2}$')])),
                ('alpha3', models.CharField(help_text='ISO 3166-1 Three-letter code', max_length=3, unique=True, validators=[django.core.validators.RegexValidator(message='Country Alpha-3 code must be exactly 3 uppercase alphabetic characters', regex='^[A-Z]{3}$')])),
                ('numeric', models.CharField(blank=True, help_text='ISO 3166-1 numeric code', max_length=3, null=True, unique=True, validators=[django.core.validators.RegexValidator(message='Country Numeric code must be exactly 3 digits', regex='^\\\\d{3}$')])),
            ],
            options={
                'verbose_name_plural': 'countries',
                'ordering': ('alpha2',),
            },
        ),
        migrations.CreateModel(
            name='CountryRegion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.Country')),
            ],
            options={
                'verbose_name': 'country region',
                'ordering': ('country', 'name'),
            },
        ),
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(choices=[('LOCAL', 'Local'), ('CHIPIN', 'ChipIn'), ('PAYPAL', 'PayPal')], default='LOCAL', max_length=255)),
                ('domainId', models.CharField(blank=True, editable=False, max_length=160, unique=True)),
                ('transactionstate', models.CharField(choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ('FLAGGED', 'Flagged')], db_index=True, default='PENDING', max_length=64, verbose_name='Transaction State')),
                ('bidstate', models.CharField(choices=[('PENDING', 'Pending'), ('IGNORED', 'Ignored'), ('PROCESSED', 'Processed'), ('FLAGGED', 'Flagged')], db_index=True, default='PENDING', max_length=255, verbose_name='Bid State')),
                ('readstate', models.CharField(choices=[('PENDING', 'Pending'), ('READY', 'Ready to Read'), ('IGNORED', 'Ignored'), ('READ', 'Read'), ('FLAGGED', 'Flagged')], db_index=True, default='PENDING', max_length=255, verbose_name='Read State')),
                ('commentstate', models.CharField(choices=[('ABSENT', 'Absent'), ('PENDING', 'Pending'), ('DENIED', 'Denied'), ('APPROVED', 'Approved'), ('FLAGGED', 'Flagged')], db_index=True, default='ABSENT', max_length=255, verbose_name='Comment State')),
                ('amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Donation Amount')),
                ('fee', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=20, validators=[tracker.validators.positive], verbose_name='Donation Fee')),
                ('currency', models.CharField(choices=[('USD', 'US Dollars'), ('CAD', 'Canadian Dollars')], max_length=8, verbose_name='Currency')),
                ('timereceived', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Time Received')),
                ('comment', models.TextField(blank=True, verbose_name='Comment')),
                ('modcomment', models.TextField(blank=True, verbose_name='Moderator Comment')),
                ('testdonation', models.BooleanField(default=False)),
                ('requestedvisibility', models.CharField(choices=[('CURR', 'Use Existing (Anonymous if not set)'), ('FULL', 'Fully Visible'), ('FIRST', 'First Name, Last Initial'), ('ALIAS', 'Alias Only'), ('ANON', 'Anonymous')], default='CURR', max_length=32, verbose_name='Requested Visibility')),
                ('requestedalias', models.CharField(blank=True, max_length=32, null=True, verbose_name='Requested Alias')),
                ('requestedemail', models.EmailField(blank=True, max_length=128, null=True, verbose_name='Requested Contact Email')),
                ('requestedsolicitemail', models.CharField(choices=[('CURR', 'Use Existing (Opt Out if not set)'), ('OPTOUT', 'Opt Out'), ('OPTIN', 'Opt In')], default='CURR', max_length=32, verbose_name='Requested Charity Email Opt In')),
                ('commentlanguage', models.CharField(choices=[('un', 'Unknown'), ('en', 'English'), ('fr', 'French'), ('de', 'German')], default='un', max_length=32, verbose_name='Comment Language')),
            ],
            options={
                'ordering': ['-timereceived'],
                'permissions': (('delete_all_donations', 'Can delete non-local donations'), ('view_full_list', 'Can view full donation list'), ('view_comments', 'Can view all comments'), ('view_pending', 'Can view pending donations'), ('view_test', 'Can view test donations'), ('send_to_reader', 'Can send donations to the reader')),
                'get_latest_by': 'timereceived',
            },
        ),
        migrations.CreateModel(
            name='DonationBid',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero])),
                ('bid', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bids', to='tracker.Bid')),
                ('donation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bids', to='tracker.Donation')),
            ],
            options={
                'verbose_name': 'Donation Bid',
                'ordering': ['-donation__timereceived'],
            },
        ),
        migrations.CreateModel(
            name='Donor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=128, verbose_name='Contact Email')),
                ('alias', models.CharField(blank=True, max_length=32, null=True)),
                ('firstname', models.CharField(blank=True, max_length=64, verbose_name='First Name')),
                ('lastname', models.CharField(blank=True, max_length=64, verbose_name='Last Name')),
                ('visibility', models.CharField(choices=[('FULL', 'Fully Visible'), ('FIRST', 'First Name, Last Initial'), ('ALIAS', 'Alias Only'), ('ANON', 'Anonymous')], default='FIRST', max_length=32)),
                ('addresscity', models.CharField(blank=True, max_length=128, verbose_name='City')),
                ('addressstreet', models.CharField(blank=True, max_length=128, verbose_name='Street/P.O. Box')),
                ('addressstate', models.CharField(blank=True, max_length=128, verbose_name='State/Province')),
                ('addresszip', models.CharField(blank=True, max_length=128, verbose_name='Zip/Postal Code')),
                ('paypalemail', models.EmailField(blank=True, max_length=128, null=True, unique=True, verbose_name='Paypal Email')),
                ('solicitemail', models.CharField(choices=[('CURR', 'Use Existing (Opt Out if not set)'), ('OPTOUT', 'Opt Out'), ('OPTIN', 'Opt In')], default='CURR', max_length=32)),
                ('addresscountry', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='tracker.Country', verbose_name='Country')),
                ('user', tracker.models.fields.OneToOneOrNoneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['lastname', 'firstname', 'email'],
                'permissions': (('delete_all_donors', 'Can delete donors with cleared donations'), ('view_usernames', 'Can view full usernames'), ('view_emails', 'Can view email addresses')),
            },
        ),
        migrations.CreateModel(
            name='DonorCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('donation_total', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero])),
                ('donation_count', models.IntegerField(default=0, editable=False, validators=[tracker.validators.positive, tracker.validators.nonzero])),
                ('donation_avg', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero])),
                ('donation_max', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero])),
                ('donor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.Donor')),
            ],
            options={
                'ordering': ('donor',),
            },
        ),
        migrations.CreateModel(
            name='DonorPrizeEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.DecimalField(decimal_places=2, default=Decimal('1.0'), help_text='This is the weight to apply this entry in the drawing (if weight is applicable).', max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Entry Weight')),
                ('donor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.Donor')),
            ],
            options={
                'verbose_name': 'Donor Prize Entry',
                'verbose_name_plural': 'Donor Prize Entries',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short', models.CharField(max_length=64, unique=True)),
                ('name', models.CharField(max_length=128)),
                ('receivername', models.CharField(blank=True, max_length=128, verbose_name='Receiver Name')),
                ('targetamount', models.DecimalField(decimal_places=2, max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Target Amount')),
                ('minimumdonation', models.DecimalField(decimal_places=2, default=Decimal('1.00'), help_text='Enforces a minimum donation amount on the donate page.', max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Minimum Donation')),
                ('usepaypalsandbox', models.BooleanField(default=False, verbose_name='Use Paypal Sandbox')),
                ('paypalemail', models.EmailField(max_length=128, verbose_name='Receiver Paypal')),
                ('paypalcurrency', models.CharField(choices=[('USD', 'US Dollars'), ('CAD', 'Canadian Dollars')], default='USD', max_length=8, verbose_name='Currency')),
                ('donationemailsender', models.EmailField(blank=True, max_length=128, null=True, verbose_name='Donation Email Sender')),
                ('scheduleid', models.CharField(blank=True, editable=False, max_length=128, null=True, unique=True, verbose_name='Schedule ID (LEGACY)')),
                ('date', models.DateField()),
                ('timezone', timezone_field.fields.TimeZoneField(default='US/Eastern')),
                ('locked', models.BooleanField(default=False, help_text='Requires special permission to edit this event or anything associated with it')),
                ('prize_accept_deadline_delta', models.IntegerField(default=14, help_text='The number of days a winner will be given to accept a prize before it is re-rolled.', validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Prize Accept Deadline Delta')),
                ('allowed_prize_countries', models.ManyToManyField(blank=True, help_text='List of countries whose residents are allowed to receive prizes (leave blank to allow all countries)', to='tracker.Country', verbose_name='Allowed Prize Countries')),
                ('disallowed_prize_regions', models.ManyToManyField(blank=True, help_text='A blacklist of regions within allowed countries that are not allowed for drawings (e.g. Quebec in Canada)', to='tracker.CountryRegion', verbose_name='Disallowed Regions')),
                ('donationemailtemplate', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='event_donation_templates', to='post_office.EmailTemplate', verbose_name='Donation Email Template')),
                ('pendingdonationemailtemplate', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='event_pending_donation_templates', to='post_office.EmailTemplate', verbose_name='Pending Donation Email Template')),
                ('prizecontributoremailtemplate', models.ForeignKey(blank=True, default=None, help_text="Email template to use when responding to prize contributor's submission requests", null=True, on_delete=django.db.models.deletion.PROTECT, related_name='event_prizecontributortemplates', to='post_office.EmailTemplate', verbose_name='Prize Contributor Accept/Deny Email Template')),
                ('prizecoordinator', models.ForeignKey(blank=True, default=None, help_text='The person responsible for managing prize acceptance/distribution', null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Prize Coordinator')),
                ('prizeshippedemailtemplate', models.ForeignKey(blank=True, default=None, help_text='Email template to use when the aprize has been shipped to its recipient).', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='event_prizeshippedtemplates', to='post_office.EmailTemplate', verbose_name='Prize Shipped Email Template')),
                ('prizewinneracceptemailtemplate', models.ForeignKey(blank=True, default=None, help_text='Email template to use when someone accepts a prize (and thus it needs to be shipped).', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='event_prizewinneraccepttemplates', to='post_office.EmailTemplate', verbose_name='Prize Accepted Email Template')),
                ('prizewinneremailtemplate', models.ForeignKey(blank=True, default=None, help_text='Email template to use when someone wins a prize.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='event_prizewinnertemplates', to='post_office.EmailTemplate', verbose_name='Prize Winner Email Template')),
            ],
            options={
                'ordering': ('date',),
                'permissions': (('can_edit_locked_events', 'Can edit locked events'),),
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Timestamp')),
                ('category', models.CharField(default='other', max_length=64, verbose_name='Category')),
                ('message', models.TextField(blank=True, verbose_name='Message')),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='tracker.Event')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Log',
                'ordering': ['-timestamp'],
                'permissions': (('can_view_log', 'Can view tracker logs'), ('can_change_log', 'Can change tracker logs')),
            },
        ),
        migrations.CreateModel(
            name='PostbackURL',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(verbose_name='URL')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='postbacks', to='tracker.Event', verbose_name='Event')),
            ],
        ),
        migrations.CreateModel(
            name='Prize',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('image', models.URLField(blank=True, max_length=1024, null=True)),
                ('altimage', models.URLField(blank=True, help_text='A second image to display in situations where the default image is not appropriate (tight spaces, stream, etc...)', max_length=1024, null=True, verbose_name='Alternate Image')),
                ('imagefile', models.FileField(blank=True, null=True, upload_to='prizes')),
                ('description', models.TextField(blank=True, max_length=1024, null=True)),
                ('shortdescription', models.TextField(blank=True, help_text='Alternative description text to display in tight spaces', max_length=256, verbose_name='Short Description')),
                ('extrainfo', models.TextField(blank=True, max_length=1024, null=True)),
                ('estimatedvalue', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Estimated Value')),
                ('minimumbid', models.DecimalField(decimal_places=2, default=Decimal('5.0'), max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Minimum Bid')),
                ('maximumbid', models.DecimalField(blank=True, decimal_places=2, default=Decimal('5.0'), max_digits=20, null=True, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Maximum Bid')),
                ('sumdonations', models.BooleanField(default=False, verbose_name='Sum Donations')),
                ('randomdraw', models.BooleanField(default=True, verbose_name='Random Draw')),
                ('ticketdraw', models.BooleanField(default=False, verbose_name='Ticket Draw')),
                ('starttime', models.DateTimeField(blank=True, null=True, verbose_name='Start Time')),
                ('endtime', models.DateTimeField(blank=True, null=True, verbose_name='End Time')),
                ('maxwinners', models.IntegerField(default=1, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Max Winners')),
                ('maxmultiwin', models.IntegerField(default=1, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Max Wins per Donor')),
                ('provider', models.CharField(blank=True, help_text='Name of the person who provided the prize to the event', max_length=64)),
                ('acceptemailsent', models.BooleanField(default=False, verbose_name='Accept/Deny Email Sent')),
                ('creator', models.CharField(blank=True, max_length=64, null=True, verbose_name='Creator')),
                ('creatoremail', models.EmailField(blank=True, max_length=128, null=True, verbose_name='Creator Email')),
                ('creatorwebsite', models.CharField(blank=True, max_length=128, null=True, verbose_name='Creator Website')),
                ('state', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('DENIED', 'Denied'), ('FLAGGED', 'Flagged')], default='PENDING', max_length=32)),
                ('requiresshipping', models.BooleanField(default=True, verbose_name='Requires Postal Shipping')),
                ('reviewnotes', models.TextField(blank=True, help_text='Notes for the contributor (for example, why a particular prize was denied)', max_length=1024, verbose_name='Review Notes')),
                ('custom_country_filter', models.BooleanField(default=False, help_text='If checked, use a different country filter than that of the event.', verbose_name='Use Custom Country Filter')),
                ('allowed_prize_countries', models.ManyToManyField(blank=True, help_text='List of countries whose residents are allowed to receive prizes (leave blank to allow all countries)', to='tracker.Country', verbose_name='Prize Countries')),
            ],
            options={
                'ordering': ['event__date', 'startrun__starttime', 'starttime', 'name'],
            },
        ),
        migrations.CreateModel(
            name='PrizeCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
            ],
            options={
                'verbose_name': 'Prize Category',
                'verbose_name_plural': 'Prize Categories',
            },
        ),
        migrations.CreateModel(
            name='PrizeTicket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=20, validators=[tracker.validators.positive, tracker.validators.nonzero])),
                ('donation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tickets', to='tracker.Donation')),
                ('prize', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tickets', to='tracker.Prize')),
            ],
            options={
                'verbose_name': 'Prize Ticket',
                'ordering': ['-donation__timereceived'],
            },
        ),
        migrations.CreateModel(
            name='PrizeWinner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pendingcount', models.IntegerField(default=1, help_text='The number of pending wins this donor has on this prize.', validators=[tracker.validators.positive], verbose_name='Pending Count')),
                ('acceptcount', models.IntegerField(default=0, help_text='The number of copied this winner has won and accepted.', validators=[tracker.validators.positive], verbose_name='Accept Count')),
                ('declinecount', models.IntegerField(default=0, help_text='The number of declines this donor has put towards this prize. Set it to the max prize multi win amount to prevent this donor from being entered from future drawings.', validators=[tracker.validators.positive], verbose_name='Decline Count')),
                ('sumcount', models.IntegerField(default=1, editable=False, help_text='The total number of prize instances associated with this winner', validators=[tracker.validators.positive], verbose_name='Sum Counts')),
                ('emailsent', models.BooleanField(default=False, verbose_name='Notification Email Sent')),
                ('acceptemailsentcount', models.IntegerField(default=0, help_text='The number of accepts that the previous e-mail was sent for (or 0 if none were sent yet).', validators=[tracker.validators.positive], verbose_name='Accept Count Sent For')),
                ('shippingemailsent', models.BooleanField(default=False, verbose_name='Shipping Email Sent')),
                ('couriername', models.CharField(blank=True, help_text='e.g. FedEx, DHL, ...', max_length=64, verbose_name='Courier Service Name')),
                ('trackingnumber', models.CharField(blank=True, max_length=64, verbose_name='Tracking Number')),
                ('shippingstate', models.CharField(choices=[('PENDING', 'Pending'), ('SHIPPED', 'Shipped')], default='PENDING', max_length=64, verbose_name='Shipping State')),
                ('shippingcost', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, validators=[tracker.validators.positive, tracker.validators.nonzero], verbose_name='Shipping Cost')),
                ('winnernotes', models.TextField(blank=True, max_length=1024, verbose_name='Winner Notes')),
                ('shippingnotes', models.TextField(blank=True, max_length=2048, verbose_name='Shipping Notes')),
                ('acceptdeadline', models.DateTimeField(blank=True, default=None, help_text='The deadline for this winner to accept their prize (leave blank for no deadline)', null=True, verbose_name='Winner Accept Deadline')),
                ('auth_code', models.CharField(default=tracker.util.make_auth_code, editable=False, help_text='Used instead of a login for winners to manage prizes.', max_length=64)),
                ('shipping_receipt_url', models.URLField(blank=True, help_text='The URL of an image of the shipping receipt', max_length=1024, verbose_name='Shipping Receipt Image URL')),
                ('prize', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.Prize')),
                ('winner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.Donor')),
            ],
            options={
                'verbose_name': 'Prize Winner',
            },
        ),
        migrations.CreateModel(
            name='Runner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('stream', models.URLField(blank=True, max_length=128)),
                ('twitter', models.SlugField(blank=True, max_length=15)),
                ('youtube', models.SlugField(blank=True, max_length=20)),
                ('donor', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='tracker.Donor')),
            ],
        ),
        migrations.CreateModel(
            name='SpeedRun',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('display_name', models.TextField(blank=True, help_text='How to display this game on the stream.', max_length=256, verbose_name='Display Name')),
                ('deprecated_runners', models.CharField(blank=True, editable=False, max_length=1024, validators=[tracker.models.event.runners_exists], verbose_name='*DEPRECATED* Runners')),
                ('console', models.CharField(blank=True, max_length=32)),
                ('commentators', models.CharField(blank=True, max_length=1024)),
                ('description', models.TextField(blank=True, max_length=1024)),
                ('starttime', models.DateTimeField(editable=False, null=True, verbose_name='Start Time')),
                ('endtime', models.DateTimeField(editable=False, null=True, verbose_name='End Time')),
                ('order', models.IntegerField(editable=False, null=True)),
                ('run_time', tracker.models.event.TimestampField()),
                ('setup_time', tracker.models.event.TimestampField()),
                ('coop', models.BooleanField(default=False, help_text='Cooperative runs should be marked with this for layout purposes')),
                ('category', models.CharField(blank=True, help_text='The type of run being performed', max_length=64, null=True)),
                ('release_year', models.IntegerField(blank=True, help_text='The year the game was released', null=True, verbose_name='Release Year')),
                ('giantbomb_id', models.IntegerField(blank=True, help_text='Identifies the game in the GiantBomb database, to allow auto-population of game data.', null=True, verbose_name='GiantBomb Database ID')),
                ('tech_notes', models.TextField(blank=True, help_text='Notes for the tech crew')),
                ('event', models.ForeignKey(default=tracker.models.event.LatestEvent, on_delete=django.db.models.deletion.PROTECT, to='tracker.Event')),
                ('runners', models.ManyToManyField(to='tracker.Runner')),
            ],
            options={
                'verbose_name': 'Speed Run',
                'ordering': ['event__date', 'order'],
                'permissions': (('can_view_tech_notes', 'Can view tech notes'),),
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('external_id', models.IntegerField(primary_key=True, serialize=False)),
                ('game_name', models.CharField(max_length=64)),
                ('category', models.CharField(max_length=64)),
                ('console', models.CharField(max_length=32)),
                ('estimate', tracker.models.event.TimestampField()),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.SpeedRun')),
                ('runner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.Runner')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prepend', models.CharField(blank=True, max_length=64, verbose_name='Template Prepend')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Profile',
                'permissions': (('show_rendertime', 'Can view page render times'), ('show_queries', 'Can view database queries'), ('can_search', 'Can use search url')),
            },
        ),
        migrations.AddField(
            model_name='prize',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='tracker.PrizeCategory'),
        ),
        migrations.AddField(
            model_name='prize',
            name='disallowed_prize_regions',
            field=models.ManyToManyField(blank=True, help_text='A blacklist of regions within allowed countries that are not allowed for drawings (e.g. Quebec in Canada)', to='tracker.CountryRegion', verbose_name='Disallowed Regions'),
        ),
        migrations.AddField(
            model_name='prize',
            name='endrun',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='prize_end', to='tracker.SpeedRun', verbose_name='End Run'),
        ),
        migrations.AddField(
            model_name='prize',
            name='event',
            field=models.ForeignKey(default=tracker.models.event.LatestEvent, on_delete=django.db.models.deletion.PROTECT, to='tracker.Event'),
        ),
        migrations.AddField(
            model_name='prize',
            name='handler',
            field=models.ForeignKey(help_text='User account responsible for prize shipping', null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='prize',
            name='startrun',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='prize_start', to='tracker.SpeedRun', verbose_name='Start Run'),
        ),
        migrations.AddField(
            model_name='donorprizeentry',
            name='prize',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tracker.Prize'),
        ),
        migrations.AddField(
            model_name='donorcache',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='tracker.Event'),
        ),
        migrations.AddField(
            model_name='donation',
            name='donor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='tracker.Donor'),
        ),
        migrations.AddField(
            model_name='donation',
            name='event',
            field=models.ForeignKey(default=tracker.models.event.LatestEvent, on_delete=django.db.models.deletion.PROTECT, to='tracker.Event'),
        ),
        migrations.AddField(
            model_name='bid',
            name='event',
            field=models.ForeignKey(blank=True, help_text='Required for top level bids if Run is not set', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='bids', to='tracker.Event', verbose_name='Event'),
        ),
        migrations.AddField(
            model_name='bid',
            name='parent',
            field=mptt.fields.TreeForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='options', to='tracker.Bid', verbose_name='Parent'),
        ),
        migrations.AddField(
            model_name='bid',
            name='speedrun',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='bids', to='tracker.SpeedRun', verbose_name='Run'),
        ),
        migrations.AlterUniqueTogether(
            name='speedrun',
            unique_together={('name', 'category', 'event'), ('event', 'order')},
        ),
        migrations.AlterUniqueTogether(
            name='prizewinner',
            unique_together={('prize', 'winner')},
        ),
        migrations.AlterUniqueTogether(
            name='prizeticket',
            unique_together={('prize', 'donation')},
        ),
        migrations.AlterUniqueTogether(
            name='prize',
            unique_together={('name', 'event')},
        ),
        migrations.AlterUniqueTogether(
            name='donorprizeentry',
            unique_together={('prize', 'donor')},
        ),
        migrations.AlterUniqueTogether(
            name='donorcache',
            unique_together={('event', 'donor')},
        ),
        migrations.AlterUniqueTogether(
            name='donationbid',
            unique_together={('bid', 'donation')},
        ),
        migrations.AlterUniqueTogether(
            name='countryregion',
            unique_together={('name', 'country')},
        ),
        migrations.AlterUniqueTogether(
            name='bid',
            unique_together={('event', 'name', 'speedrun', 'parent')},
        ),
    ]
