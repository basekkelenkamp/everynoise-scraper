from flask_assets import Bundle


bundles = {
    "home_css": Bundle(
        "css/main.scss",
        depends="css/*.scss",
        filters="libsass",
        output="gen/home.%(version)s.css",
    )
}
