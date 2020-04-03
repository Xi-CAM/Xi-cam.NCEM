import mimetypes

mimetypes.add_type('application/x-DM', '.dm3')
mimetypes.add_type('application/x-DM', '.dm4')
mimetypes.add_type('application/x-SER', '.ser')
mimetypes.add_type('application/x-EMD', '.emd')
mimetypes.add_type('application/x-EMD-VELOX', '.emd')
_extensions = ['.mrc', '.rec', '.ali', '.st']
for extension in _extensions:
    mimetypes.add_type('application/x-MRC', extension)
