from flask_assets import Bundle
# from webassets.filter import get_filter
#
# libsass = get_filter(
#     'libsass',
#     as_output=True,
#     style='compressed',
# )

bundles = {
    'home_css': Bundle(
        'css/main.scss',
        depends='css/*.scss',
        filters='libsass',
        output='gen/home.%(version)s.css')
}