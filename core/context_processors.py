def navigation(request):
    if request.user.is_authenticated and request.user.is_staff:
        return {"nav_items":[("Overview","dashboard"),("Customers","customer_list"),("Admissions","admission_list"),("Applications","application_list"),("Training","training_list"),("Employees","employee_list"),("Salaries","salary_list"),("Vehicles","vehicle_list"),("Payments","payment_list"),("RTO services","service_request_list"),("Reports","reports")]}
    return {"nav_items":[]}
