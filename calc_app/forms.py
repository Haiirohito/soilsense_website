from django import forms


class CoordinateForm(forms.Form):
    latitude = forms.FloatField()
    longitude = forms.FloatField()
    radius = forms.FloatField()


class GeoJSONUploadForm(forms.Form):
    geojson_file = forms.FileField()
