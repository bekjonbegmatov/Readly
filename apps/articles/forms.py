from django import forms
from .models import Article, Comment


class ArticleForm(forms.ModelForm):
    tags_input = forms.CharField(required=False, help_text="Через запятую: например, tech, ios")

    class Meta:
        model = Article
        fields = ["title", "content", "cover"]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]