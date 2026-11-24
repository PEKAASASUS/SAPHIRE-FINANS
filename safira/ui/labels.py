import customtkinter as ctk


class SapphireLabel(ctk.CTkLabel):
    """Release subscriptions so cached CTkImages do not retain destroyed views."""
    def destroy(self):
        image=getattr(self,'_image',None)
        if isinstance(image,ctk.CTkImage):
            try:image.remove_configure_callback(self._update_image)
            except ValueError:pass
        super().destroy()
