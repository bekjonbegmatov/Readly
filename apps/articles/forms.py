from django import forms
from .models import Article, Comment


class ArticleForm(forms.ModelForm):
    cover_url = forms.URLField(
        required=False,
        help_text="Вставьте ссылку на изображение (JPEG/PNG/WebP)",
        widget=forms.URLInput(attrs={
            'placeholder': 'https://...',
            'class': 'w-full rounded-md border border-gray-300 bg-white px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
        })
    )
    tags_input = forms.CharField(
        required=False,
        help_text="Через запятую: например, tech, ios",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
        })
    )

    class Meta:
        model = Article
        fields = ["title", "content", "cover"]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full min-h-[180px] rounded-md border border-gray-300 bg-gray-50 px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
            }),
            'cover': forms.ClearableFileInput(attrs={
                'class': 'w-full rounded-md border border-gray-300 bg-white px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'w-full min-h-[80px] rounded-md border border-gray-300 bg-gray-50 px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
            })
        }