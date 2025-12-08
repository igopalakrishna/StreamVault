"""
CS-GY 6083 - Project Part II
Informational Pages Routes

Routes for footer links: About, Careers, Press, Legal, Support, etc.
"""

from flask import Blueprint, render_template

info_bp = Blueprint('info', __name__)


@info_bp.route('/about')
def about():
    """About Us page"""
    return render_template('info/about.html')


@info_bp.route('/careers')
def careers():
    """Careers page"""
    return render_template('info/careers.html')


@info_bp.route('/press')
def press():
    """Press/Media page"""
    return render_template('info/press.html')


@info_bp.route('/investor-relations')
def investor_relations():
    """Investor Relations page"""
    return render_template('info/investor_relations.html')


@info_bp.route('/help-center')
def help_center():
    """Help Center/Support page"""
    return render_template('info/help_center.html')


@info_bp.route('/media-center')
def media_center():
    """Media Center page"""
    return render_template('info/media_center.html')


@info_bp.route('/contact')
def contact():
    """Contact Us page"""
    return render_template('info/contact.html')


@info_bp.route('/terms-of-use')
def terms_of_use():
    """Terms of Use page"""
    return render_template('info/terms.html')


@info_bp.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('info/privacy.html')


@info_bp.route('/cookie-policy')
def cookie_policy():
    """Cookie Policy page"""
    return render_template('info/cookies.html')


@info_bp.route('/corporate-information')
def corporate_information():
    """Corporate Information page"""
    return render_template('info/corporate.html')

