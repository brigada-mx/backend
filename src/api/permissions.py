from rest_framework import permissions

READABLE_NURSE_INCIDENT_CATEGORIES = (0,1,2,7,)


class HasNurseOwner(permissions.BasePermission):
    """Allow staff, or nurse associated with object, or anyone if object's nurse
    is null.
    """
    def has_object_permission(self, request, view, obj):
        if request.auth == "NurseUser":
            try:
                return obj.nurse.pk == request.user.pk
            except AttributeError:
                return False
        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False


class HasNoNurseOwner(permissions.BasePermission):
    """Allow staff or nurse user to edit if object's nurse is null.
    """
    def has_object_permission(self, request, view, obj):
        if request.auth == "NurseUser":
            try:
                return obj.nurse is None
            except AttributeError:
                return False
        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False


class IsNurseUser(permissions.BasePermission):
    """Allow nurse to edit only itself.
    """
    def has_object_permission(self, request, view, obj):
        if request.auth == "NurseUser":
            try:
                return obj.pk == request.user.pk
            except:
                return False
        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False


class IsReadableNurseIncidentCategory(permissions.BasePermission):
    """Allow nurses to access a `ShiftIncident` instance only if
    its `category` is in a list of accepted categories.
    """
    def has_object_permission(self, request, view, obj):
        if request.auth == "NurseUser":
            try:
                return obj.category in READABLE_NURSE_INCIDENT_CATEGORIES
            except AttributeError:
                return False
        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False


class HasShiftWithNurseOwner(permissions.BasePermission):
    """Allow staff, or nurse associated with shift to
    which object has been assigned.
    """
    def has_object_permission(self, request, view, obj):
        if request.auth == "NurseUser":
            try:
                return obj.shift.nurse.pk == request.user.pk
            except AttributeError:
                return False
        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False


class IsClientUser(permissions.BasePermission):
    """Allow client to edit only itself, unless it's the owner of the account.
    """
    def has_object_permission(self, request, view, obj):
        if request.auth == "ClientUser":
            client = request.user
            if client.account_holder: # `account_holder` can edit objects that belong to his account
                return obj.reservation.pk == client.reservation.pk
            try:
                return obj.pk == request.user.pk
            except:
                return False
        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False


class HasClientOwner(permissions.BasePermission):
    """Allow staff, or client account holder whose account contains object.
    """
    def has_permission(self, request, view):
        """This method is necessary to restrict access to object creation views,
        because `has_object_permission` is not invoked for newly created objects.
        """
        if request.auth == "ClientUser":
            return request.user.account_holder == True
        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False

    def has_object_permission(self, request, view, obj):
        if request.auth == "ClientUser":
            client = request.user
            try:
                return obj.reservation.pk == client.reservation.pk
            except AttributeError:
                return False
        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False


class HasOwner(permissions.BasePermission):
    """Allow staff, or nurse associated with object, or client whose account
    contains object.
    """
    def has_object_permission(self, request, view, obj):
        if request.auth == "NurseUser":
            try:
                return obj.nurse.pk == request.user.pk
            except AttributeError:
                return False

        if request.auth == "ClientUser":
            client = request.user
            try:
                return obj.reservation.pk == client.reservation.pk
            except AttributeError:
                return False

        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False


class HasClient(permissions.BasePermission):
    """Allow staff, or client whose account contains object.
    """
    def has_object_permission(self, request, view, obj):
        if request.auth == "ClientUser":
            client = request.user
            try:
                return obj.reservation.pk == client.reservation.pk
            except AttributeError:
                return False
        if hasattr(request.user, 'is_staff'):
            return request.user.is_staff
        return False
