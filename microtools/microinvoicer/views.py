"""How about now."""

from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView

from django_registration.backends.one_step.views import RegistrationView

from . import forms
from . import micro_use_cases as muc


class IndexView(TemplateView):
    """Bla Bla."""

    template_name = 'index.html'


class MicroRegistrationView(RegistrationView):
    """Bla Bla."""

    template_name = 'registration_form.html'
    form_class = forms.MicroRegistrationForm
    # For now, we redirect straight to fiscal information view after signup.
    # When we'll change to two step registration, fiscal form will be shown at
    # the first login
    success_url = reverse_lazy('microinvoicer_setup')


class MicroLoginView(LoginView):
    """Bla Bla."""

    template_name = 'login.html'


class MicroHomeView(LoginRequiredMixin, TemplateView):
    """Bla Bla."""

    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        """Bla Bla."""
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            db = self.request.user.read_data()
            context['seller'] = {'name': db.register.seller.name}
            context['contracts'] = db.flatten_contracts()
            context['invoices'] = db.invoices()

        return context


class BaseFormView(LoginRequiredMixin, FormView):
    """Extend this view for any form."""

    template_name = 'base_form.html'
    success_url = reverse_lazy('microinvoicer_home')

    def get_context_data(self, **kwargs):
        """Bla Bla."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = self.form_title
        return context

    def get_form_kwargs(self):
        """Bla Bla."""
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


class SellerView(BaseFormView):
    """
    Updates user's fiscal information.

    ATTENTION: any previous user data will be erased
    TODO: check if there was any data before
    """

    form_title = 'Setup fiscal information'
    form_class = forms.SellerForm

    def form_valid(self, form):
        """Bla Bla."""
        db = muc.create_empty_db(form.cleaned_data)
        self.request.user.write_data(db)
        return super().form_valid(form)


class ContractView(BaseFormView):
    """Contract details."""

    form_title = 'Buyer contract details'
    form_class = forms.ContractForm

    def form_valid(self, form):
        """Bla Bla."""
        db = form.user['db']
        contract = muc.create_contract(form.cleaned_data)
        db.contracts.append(contract)
        self.request.user.write_data(db)
        return super().form_valid(form)


class ContractsView(LoginRequiredMixin, ListView):
    """Contracts manager."""

    template_name = 'contract_list.html'

    def get_queryset(self):
        """Bla Bla."""
        db = self.request.user.read_data()
        return db.flatten_contracts() if db else []


class DraftInvoiceView(BaseFormView):
    """Creates a new draft invoice."""

    form_title = 'Generate new draft invoice'
    form_class = forms.InvoiceForm

    def form_valid(self, form):
        """Bla Bla."""
        db = form.user['db']
        db = muc.draft_time_invoice(db, form.cleaned_data)
        self.request.user.write_data(db)

        return super().form_valid(form)


class TimeInvoiceView(BaseFormView):
    """Allows to mess up with a time invoice."""

    form_title = 'Time Invoice'
    form_class = forms.InvoiceForm

    def get_initial(self):
        """we need this data"""
        initial = super().get_initial()
        invoices = self.request.user.read_data().invoices()

        try:
            ndx = int(self.kwargs['invoice_id']) - 1
            invoice = invoices[ndx]
        except (IndexError, KeyError):
            raise Http404
        finally:
            initial['duration'] = invoice.activity.duration
            initial['flavor'] = invoice.activity.flavor
            initial['project_id'] = invoice.activity.project_id
            initial['xchg_rate'] = invoice.conversion_rate

        return initial


    def form_valid(self, form):
        """Bla Bla."""
        db = form.user['db']
        db = muc.draft_time_invoice(db, form.cleaned_data)
        print(form.cleaned_data)
        self.request.user.write_data(db)
        
        return super().form_valid(form)



class ProfileView(BaseFormView):
    """Bla Bla."""

    template_name = 'profile.html'
    form_title = 'Your Profile'
    form_class = forms.ProfileForm
