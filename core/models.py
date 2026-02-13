from django.db import models
import uuid

class WebhookLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    sender_ip = models.CharField(max_length=50, blank=True, null=True)
    method = models.CharField(max_length=10)
    headers = models.JSONField(default=dict)
    body = models.JSONField(default=dict, blank=True, null=True)
    raw_body = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.timestamp} - {self.method} - {self.id}"

    class Meta:
        ordering = ['-timestamp']
