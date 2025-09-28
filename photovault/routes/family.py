# photovault/routes/family.py

import logging
import os
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, abort
from flask_login import login_required, current_user
from photovault.models import (
    db, User, FamilyVault, FamilyMember, VaultInvitation, Story, 
    VaultPhoto, StoryPhoto, StoryPerson, Photo, Person
)
from photovault.forms import (
    validate_vault_name, validate_vault_description, validate_email_for_invitation,
    validate_invitation_role, validate_story_title, validate_story_content,
    validate_story_type, generate_vault_code, generate_invitation_token,
    get_invitation_expiry, validate_vault_code, validate_photo_caption
)
from photovault.services.montage_service import create_montage
from photovault.utils.enhanced_file_handler import delete_file_enhanced

# Configure logging
logger = logging.getLogger(__name__)

def send_invitation_email(email, invitation_token, vault_name, inviter_name):
    """Send family vault invitation email using SendGrid service"""
    try:
        # Import SendGrid service
        from photovault.services.sendgrid_service import send_family_invitation_email
        
        # Try SendGrid first
        if send_family_invitation_email(email, invitation_token, vault_name, inviter_name):
            return True
        
        # Fallback to console logging in development if SendGrid fails
        if current_app.debug:
            invitation_url = url_for('family.accept_invitation', token=invitation_token, _external=True)
            print(f"EMAIL TO {email}: Family vault invitation link: {invitation_url}")
            current_app.logger.info(f"SendGrid failed, used console fallback for invitation to {email}")
            return True
        else:
            current_app.logger.error(f"Failed to send invitation email to {email} via SendGrid")
            return False
            
    except Exception as e:
        logger.error(f"Exception while sending invitation email to {email}: {str(e)}")
        return False

# Create blueprint
family_bp = Blueprint('family', __name__, url_prefix='/family')

@family_bp.route('/')
@login_required
def index():
    """Family vaults dashboard"""
    # Get user's vaults (created + member of)
    created_vaults = FamilyVault.query.filter_by(created_by=current_user.id).all()
    member_vaults = db.session.query(FamilyVault).join(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.status == 'active'
    ).all()
    
    # Get pending invitations
    pending_invitations = VaultInvitation.query.filter_by(
        email=current_user.email,
        status='pending'
    ).all()
    
    return render_template('family/index.html',
                         created_vaults=created_vaults,
                         member_vaults=member_vaults,
                         pending_invitations=pending_invitations)

@family_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_vault():
    """Create a new family vault"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        is_public = request.form.get('is_public') == 'on'
        
        # Validate inputs
        valid_name, name_msg = validate_vault_name(name)
        valid_desc, desc_msg = validate_vault_description(description)
        
        if not valid_name:
            flash(name_msg, 'error')
            return render_template('family/create_vault.html')
        
        if not valid_desc:
            flash(desc_msg, 'error')
            return render_template('family/create_vault.html')
        
        # Generate unique vault code
        vault_code = generate_vault_code()
        while FamilyVault.query.filter_by(vault_code=vault_code).first():
            vault_code = generate_vault_code()
        
        # Create vault
        vault = FamilyVault(
            name=name,
            description=description,
            created_by=current_user.id,
            vault_code=vault_code,
            is_public=is_public
        )
        db.session.add(vault)
        db.session.flush()  # Flush to get vault.id
        
        # Add creator as admin member
        creator_member = FamilyMember(
            vault_id=vault.id,
            user_id=current_user.id,
            role='admin',
            status='active'
        )
        db.session.add(creator_member)
        
        try:
            db.session.commit()
            flash(f'Family vault "{name}" created successfully! Share code: {vault_code}', 'success')
            return redirect(url_for('family.view_vault', vault_id=vault.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create vault: {str(e)}")
            flash('Failed to create vault. Please try again.', 'error')
    
    return render_template('family/create_vault.html')

@family_bp.route('/vault/<int:vault_id>')
@login_required
def view_vault(vault_id):
    """View family vault details"""
    vault = FamilyVault.query.get_or_404(vault_id)
    
    # Check if user has access
    if not vault.has_member(current_user.id) and vault.created_by != current_user.id:
        flash('You do not have access to this vault.', 'error')
        return redirect(url_for('family.index'))
    
    # Get vault photos
    vault_photos = VaultPhoto.query.filter_by(vault_id=vault_id).order_by(VaultPhoto.shared_at.desc()).all()
    
    # Get vault stories
    stories = Story.query.filter_by(vault_id=vault_id, is_published=True).order_by(Story.created_at.desc()).all()
    
    # Get vault members
    members = FamilyMember.query.filter_by(vault_id=vault_id, status='active').all()
    
    # Get pending invitations (only for admins and vault creator)
    user_role = vault.get_member_role(current_user.id)
    pending_invitations = []
    if user_role == 'admin' or vault.created_by == current_user.id:
        pending_invitations = VaultInvitation.query.filter_by(vault_id=vault_id, status='pending').all()
    
    return render_template('family/vault_detail.html',
                         vault=vault,
                         vault_photos=vault_photos,
                         stories=stories,
                         members=members,
                         user_role=user_role,
                         pending_invitations=pending_invitations)

@family_bp.route('/vault/<int:vault_id>/invite', methods=['GET', 'POST'])
@login_required
def invite_member(vault_id):
    """Invite a member to family vault"""
    vault = FamilyVault.query.get_or_404(vault_id)
    
    # Check if user can manage vault
    user_role = vault.get_member_role(current_user.id)
    if user_role not in ['admin'] and vault.created_by != current_user.id:
        flash('You do not have permission to invite members.', 'error')
        return redirect(url_for('family.view_vault', vault_id=vault_id))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'member')
        
        # Validate inputs
        valid_email, email_msg = validate_email_for_invitation(email)
        valid_role, role_msg = validate_invitation_role(role)
        
        if not valid_email:
            flash(email_msg, 'error')
            return render_template('family/invite_member.html', vault=vault)
        
        if not valid_role:
            flash(role_msg, 'error')
            return render_template('family/invite_member.html', vault=vault)
        
        # Check if user is already a member
        existing_member = FamilyMember.query.filter_by(vault_id=vault_id, status='active').join(User, FamilyMember.user_id == User.id).filter(User.email == email).first()
        if existing_member:
            flash('This user is already a member of the vault.', 'warning')
            return render_template('family/invite_member.html', vault=vault)
        
        # Check if invitation already exists
        existing_invitation = VaultInvitation.query.filter_by(
            vault_id=vault_id,
            email=email,
            status='pending'
        ).first()
        if existing_invitation:
            flash('An invitation has already been sent to this email.', 'warning')
            return render_template('family/invite_member.html', vault=vault)
        
        # Create invitation
        invitation = VaultInvitation(
            vault_id=vault_id,
            email=email,
            invited_by=current_user.id,
            role=role,
            invitation_token=generate_invitation_token(),
            expires_at=get_invitation_expiry()
        )
        
        try:
            db.session.add(invitation)
            db.session.commit()
            
            # Send invitation email
            email_sent = send_invitation_email(
                email=email,
                invitation_token=invitation.invitation_token,
                vault_name=vault.name,
                inviter_name=current_user.username
            )
            
            if email_sent:
                invitation.mark_as_sent()
                db.session.commit()
                flash(f'Invitation sent to {email}', 'success')
            else:
                flash(f'Invitation created but email failed to send. You can share the invitation link manually: {url_for("family.accept_invitation", token=invitation.invitation_token, _external=True)}', 'warning')
                logger.warning(f"Invitation created for {email} but email sending failed")
            
            return redirect(url_for('family.view_vault', vault_id=vault_id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create invitation: {str(e)}")
            flash('Failed to send invitation. Please try again.', 'error')
    
    return render_template('family/invite_member.html', vault=vault)

@family_bp.route('/invitation/<token>')
def accept_invitation(token):
    """Accept vault invitation"""
    invitation = VaultInvitation.query.filter_by(invitation_token=token).first_or_404()
    
    if not invitation.is_pending:
        flash('This invitation is no longer valid.', 'error')
        return redirect(url_for('main.index'))
    
    if not current_user.is_authenticated:
        # Store invitation token in session and redirect to login
        from flask import session
        session['pending_invitation'] = token
        flash('Please log in to accept the invitation.', 'info')
        return redirect(url_for('auth.login'))
    
    # Check if email matches current user
    if current_user.email.lower() != invitation.email.lower():
        flash('This invitation was sent to a different email address.', 'error')
        return redirect(url_for('family.index'))
    
    # Accept invitation
    try:
        success = invitation.accept(current_user)
        if success:
            db.session.commit()
            flash(f'Welcome to {invitation.vault.name}!', 'success')
            return redirect(url_for('family.view_vault', vault_id=invitation.vault_id))
        else:
            flash('Failed to accept invitation.', 'error')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to accept invitation: {str(e)}")
        flash('Failed to accept invitation. Please try again.', 'error')
    
    return redirect(url_for('family.index'))

@family_bp.route('/vault/<int:vault_id>/story/create', methods=['GET', 'POST'])
@login_required
def create_story(vault_id):
    """Create a new story in vault"""
    vault = FamilyVault.query.get_or_404(vault_id)
    
    # Check if user can add content
    member = FamilyMember.query.filter_by(vault_id=vault_id, user_id=current_user.id, status='active').first()
    if not member or not member.can_add_content():
        flash('You do not have permission to create stories in this vault.', 'error')
        return redirect(url_for('family.view_vault', vault_id=vault_id))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        story_type = request.form.get('story_type', 'memory')
        is_published = request.form.get('is_published', 'on') == 'on'
        
        # Validate inputs
        valid_title, title_msg = validate_story_title(title)
        valid_content, content_msg = validate_story_content(content)
        valid_type, type_msg = validate_story_type(story_type)
        
        if not valid_title:
            flash(title_msg, 'error')
            return render_template('family/create_story.html', vault=vault)
        
        if not valid_content:
            flash(content_msg, 'error')
            return render_template('family/create_story.html', vault=vault)
        
        if not valid_type:
            flash(type_msg, 'error')
            return render_template('family/create_story.html', vault=vault)
        
        # Create story
        story = Story(
            vault_id=vault_id,
            author_id=current_user.id,
            title=title,
            content=content,
            story_type=story_type,
            is_published=is_published
        )
        
        try:
            db.session.add(story)
            db.session.commit()
            flash(f'Story "{title}" created successfully!', 'success')
            return redirect(url_for('family.view_story', story_id=story.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create story: {str(e)}")
            flash('Failed to create story. Please try again.', 'error')
    
    return render_template('family/create_story.html', vault=vault)

@family_bp.route('/story/<int:story_id>')
@login_required
def view_story(story_id):
    """View a story"""
    story = Story.query.get_or_404(story_id)
    
    # Check if user has access to vault
    if not story.vault.has_member(current_user.id) and story.vault.created_by != current_user.id:
        flash('You do not have access to this story.', 'error')
        return redirect(url_for('family.index'))
    
    # Get story photos
    story_photos = StoryPhoto.query.filter_by(story_id=story_id).order_by(StoryPhoto.order_index).all()
    
    # Get story people mentions
    story_people = StoryPerson.query.filter_by(story_id=story_id).all()
    
    return render_template('family/story_detail.html',
                         story=story,
                         story_photos=story_photos,
                         story_people=story_people)

@family_bp.route('/vault/<int:vault_id>/share-photo/<int:photo_id>', methods=['POST'])
@login_required
def share_photo(vault_id, photo_id):
    """Share a photo to family vault"""
    vault = FamilyVault.query.get_or_404(vault_id)
    photo = Photo.query.get_or_404(photo_id)
    
    # Check if user can add content to vault
    member = FamilyMember.query.filter_by(vault_id=vault_id, user_id=current_user.id, status='active').first()
    if not member or not member.can_add_content():
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    # Check if user owns the photo
    if photo.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'You can only share your own photos'}), 403
    
    # Check if photo is already shared to this vault
    existing_share = VaultPhoto.query.filter_by(vault_id=vault_id, photo_id=photo_id).first()
    if existing_share:
        return jsonify({'success': False, 'error': 'Photo is already shared to this vault'}), 400
    
    caption = request.json.get('caption', '') if request.is_json else request.form.get('caption', '')
    
    # Validate caption
    valid_caption, caption_msg = validate_photo_caption(caption)
    if not valid_caption:
        return jsonify({'success': False, 'error': caption_msg}), 400
    
    # Share photo
    vault_photo = VaultPhoto(
        vault_id=vault_id,
        photo_id=photo_id,
        shared_by=current_user.id,
        caption=caption
    )
    
    try:
        db.session.add(vault_photo)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Photo shared successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to share photo: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to share photo'}), 500

@family_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join_vault():
    """Join a vault using vault code"""
    if request.method == 'POST':
        vault_code = request.form.get('vault_code', '').strip().upper()
        
        # Validate vault code
        valid_code, code_msg = validate_vault_code(vault_code)
        if not valid_code:
            flash(code_msg, 'error')
            return render_template('family/join_vault.html')
        
        # Find vault
        vault = FamilyVault.query.filter_by(vault_code=vault_code).first()
        if not vault:
            flash('Invalid vault code. Please check and try again.', 'error')
            return render_template('family/join_vault.html')
        
        # Check if already a member
        if vault.has_member(current_user.id):
            flash('You are already a member of this vault.', 'info')
            return redirect(url_for('family.view_vault', vault_id=vault.id))
        
        # Add as member
        member = FamilyMember(
            vault_id=vault.id,
            user_id=current_user.id,
            role='member',
            status='active'
        )
        
        try:
            db.session.add(member)
            db.session.commit()
            flash(f'Successfully joined "{vault.name}"!', 'success')
            return redirect(url_for('family.view_vault', vault_id=vault.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to join vault: {str(e)}")
            flash('Failed to join vault. Please try again.', 'error')
    
    return render_template('family/join_vault.html')

@family_bp.route('/vault/<int:vault_id>/add-photos', methods=['GET', 'POST'])
@login_required
def add_photos(vault_id):
    """Add photos to family vault"""
    vault = FamilyVault.query.get_or_404(vault_id)
    
    # Check if user can add content to vault
    member = FamilyMember.query.filter_by(vault_id=vault_id, user_id=current_user.id, status='active').first()
    if not member or not member.can_add_content():
        flash('You do not have permission to add photos to this vault.', 'error')
        return redirect(url_for('family.view_vault', vault_id=vault_id))
    
    if request.method == 'POST':
        # Get selected photo IDs
        photo_ids = request.form.getlist('photo_ids')
        caption = request.form.get('caption', '').strip()
        
        if not photo_ids:
            flash('Please select at least one photo to share.', 'error')
            return redirect(url_for('family.add_photos', vault_id=vault_id))
        
        shared_count = 0
        skipped_count = 0
        
        for photo_id in photo_ids:
            try:
                photo = Photo.query.filter_by(id=int(photo_id), user_id=current_user.id).first()
                if not photo:
                    continue
                
                # Check if photo is already shared to this vault
                existing_share = VaultPhoto.query.filter_by(vault_id=vault_id, photo_id=photo_id).first()
                if existing_share:
                    skipped_count += 1
                    continue
                
                # Share photo
                vault_photo = VaultPhoto(
                    vault_id=vault_id,
                    photo_id=photo_id,
                    shared_by=current_user.id,
                    caption=caption if caption else None
                )
                
                db.session.add(vault_photo)
                shared_count += 1
                
            except Exception as e:
                logger.error(f"Failed to share photo {photo_id}: {str(e)}")
                continue
        
        try:
            db.session.commit()
            
            # Create success message
            message_parts = []
            if shared_count > 0:
                message_parts.append(f'{shared_count} photo{"s" if shared_count != 1 else ""} shared successfully')
            if skipped_count > 0:
                message_parts.append(f'{skipped_count} photo{"s" if skipped_count != 1 else ""} already in vault')
            
            flash(', '.join(message_parts) + '.', 'success')
            return redirect(url_for('family.view_vault', vault_id=vault_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save shared photos: {str(e)}")
            flash('Failed to share photos. Please try again.', 'error')
    
    # GET request - show photo selection page
    page = request.args.get('page', 1, type=int)
    photos = Photo.query.filter_by(user_id=current_user.id)\
                       .order_by(Photo.created_at.desc())\
                       .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('family/add_photos.html', vault=vault, photos=photos)

@family_bp.route('/vault/<int:vault_id>/invitation/<int:invitation_id>/resend', methods=['POST'])
@login_required
def resend_invitation(vault_id, invitation_id):
    """Resend family vault invitation with rate limiting"""
    vault = FamilyVault.query.get_or_404(vault_id)
    invitation = VaultInvitation.query.get_or_404(invitation_id)
    
    # Check if invitation belongs to the vault
    if invitation.vault_id != vault_id:
        flash('Invalid invitation.', 'error')
        return redirect(url_for('family.view_vault', vault_id=vault_id))
    
    # Check if user can manage vault
    user_role = vault.get_member_role(current_user.id)
    if user_role not in ['admin'] and vault.created_by != current_user.id:
        flash('You do not have permission to resend invitations.', 'error')
        return redirect(url_for('family.view_vault', vault_id=vault_id))
    
    # Check if invitation is still pending
    if not invitation.is_pending:
        flash('This invitation is no longer pending.', 'error')
        return redirect(url_for('family.view_vault', vault_id=vault_id))
    
    # Check rate limiting (60 seconds minimum)
    if not invitation.can_resend(60):
        if invitation.last_sent_at:
            time_since_last = datetime.utcnow() - invitation.last_sent_at
            remaining_seconds = max(1, 60 - int(time_since_last.total_seconds()))
            flash(f'Please wait {remaining_seconds} more seconds before resending.', 'warning')
        else:
            flash('Unable to resend invitation at this time.', 'warning')
        return redirect(url_for('family.view_vault', vault_id=vault_id))
    
    try:
        # Resend invitation email
        email_sent = send_invitation_email(
            email=invitation.email,
            invitation_token=invitation.invitation_token,
            vault_name=vault.name,
            inviter_name=current_user.username
        )
        
        if email_sent:
            invitation.mark_as_sent()
            db.session.commit()
            flash(f'Invitation resent to {invitation.email}', 'success')
        else:
            flash(f'Failed to resend invitation to {invitation.email}. Please try again.', 'error')
            logger.warning(f"Failed to resend invitation to {invitation.email}")
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to resend invitation: {str(e)}")
        flash('Failed to resend invitation. Please try again.', 'error')
    
    return redirect(url_for('family.view_vault', vault_id=vault_id))

@family_bp.route('/api/vaults/<int:vault_id>/members/<int:member_id>/role', methods=['PUT'])
@login_required
def update_member_role(vault_id, member_id):
    """Update member role in vault"""
    vault = FamilyVault.query.get_or_404(vault_id)
    member = FamilyMember.query.get_or_404(member_id)
    
    # Check permissions
    user_role = vault.get_member_role(current_user.id)
    if user_role != 'admin' and vault.created_by != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    new_role = request.json.get('role')
    valid_role, role_msg = validate_invitation_role(new_role)
    
    if not valid_role:
        return jsonify({'success': False, 'error': role_msg}), 400
    
    try:
        member.role = new_role
        db.session.commit()
        return jsonify({'success': True, 'message': 'Member role updated'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update member role: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update role'}), 500

# Montage Routes
@family_bp.route('/vault/<int:vault_id>/montage', methods=['GET'])
@login_required
def create_montage_ui(vault_id):
    """Show montage creation interface"""
    vault = FamilyVault.query.get_or_404(vault_id)
    
    # Check if user is a member
    if not vault.has_member(current_user.id) and vault.created_by != current_user.id:
        flash('You do not have access to this vault.', 'error')
        return redirect(url_for('family.index'))
    
    # Get vault photos
    vault_photos = vault.shared_photos.all()
    
    return render_template('family/create_montage.html',
                         vault=vault,
                         vault_photos=vault_photos)

@family_bp.route('/vault/<int:vault_id>/montage', methods=['POST'])
@login_required
def create_montage_process(vault_id):
    """Process montage creation"""
    vault = FamilyVault.query.get_or_404(vault_id)
    
    # Check permissions
    user_role = vault.get_member_role(current_user.id)
    if user_role not in ['admin', 'contributor'] and vault.created_by != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    try:
        # Get selected photo IDs
        selected_ids = request.json.get('photo_ids', [])
        if len(selected_ids) < 2:
            return jsonify({'success': False, 'error': 'At least 2 photos are required'}), 400
        
        # Get montage settings
        settings = {
            'rows': int(request.json.get('rows', 2)),
            'cols': int(request.json.get('cols', 2)),
            'spacing': int(request.json.get('spacing', 10)),
            'title': request.json.get('title', ''),
            'target_width': int(request.json.get('width', 1200)),
            'target_height': int(request.json.get('height', 800))
        }
        
        # Get vault photos and build file paths
        vault_photos = VaultPhoto.query.filter(
            VaultPhoto.vault_id == vault_id,
            VaultPhoto.id.in_(selected_ids)
        ).all()
        
        if len(vault_photos) < 2:
            return jsonify({'success': False, 'error': 'Selected photos not found'}), 400
        
        # Build photo paths
        photo_paths = []
        for vault_photo in vault_photos:
            photo_paths.append(vault_photo.photo.file_path)
        
        # Create montage
        success, file_path, applied_settings = create_montage(
            photo_paths, settings, current_user.id
        )
        
        if not success:
            return jsonify({'success': False, 'error': file_path}), 500
        
        # Create new Photo record for the montage
        montage_photo = Photo(
            user_id=current_user.id,
            filename=os.path.basename(file_path),
            original_name=f"Montage_{len(vault_photos)}_photos.jpg",
            file_path=file_path,
            processing_notes=f"Montage created from {len(vault_photos)} vault photos",
            enhancement_settings=str(applied_settings),
            auto_enhanced=True,
            upload_source='montage'
        )
        db.session.add(montage_photo)
        db.session.flush()  # Get the photo ID
        
        # Share montage in vault
        vault_photo = VaultPhoto(
            vault_id=vault_id,
            photo_id=montage_photo.id,
            shared_by=current_user.id,
            caption=f"Montage of {len(vault_photos)} photos" + (f": {settings['title']}" if settings['title'] else "")
        )
        db.session.add(vault_photo)
        db.session.commit()
        
        logger.info(f"Montage created successfully for vault {vault_id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Montage created successfully!',
            'photo_id': montage_photo.id,
            'vault_photo_id': vault_photo.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create montage: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create montage'}), 500

# Photo Management Routes
@family_bp.route('/vault/<int:vault_id>/photos/<int:vault_photo_id>/unshare', methods=['POST'])
@login_required
def unshare_photo(vault_id, vault_photo_id):
    """Remove photo from vault (unshare)"""
    vault = FamilyVault.query.get_or_404(vault_id)
    vault_photo = VaultPhoto.query.get_or_404(vault_photo_id)
    
    # Verify vault_photo belongs to this vault
    if vault_photo.vault_id != vault_id:
        abort(404)
    
    # Check permissions: sharer, vault admin, or vault creator
    user_role = vault.get_member_role(current_user.id)
    can_unshare = (
        vault_photo.shared_by == current_user.id or
        user_role == 'admin' or
        vault.created_by == current_user.id
    )
    
    if not can_unshare:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    try:
        photo_name = vault_photo.photo.original_name
        db.session.delete(vault_photo)
        db.session.commit()
        
        logger.info(f"Photo {photo_name} unshared from vault {vault_id} by user {current_user.id}")
        return jsonify({
            'success': True,
            'message': f'Photo "{photo_name}" removed from vault'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to unshare photo: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to remove photo from vault'}), 500

@family_bp.route('/vault/<int:vault_id>/photos/<int:vault_photo_id>/delete_original', methods=['POST'])
@login_required
def delete_original_photo(vault_id, vault_photo_id):
    """Delete original photo file and database record"""
    vault = FamilyVault.query.get_or_404(vault_id)
    vault_photo = VaultPhoto.query.get_or_404(vault_photo_id)
    
    # Verify vault_photo belongs to this vault
    if vault_photo.vault_id != vault_id:
        abort(404)
    
    # Check permissions: only photo owner can delete original
    if vault_photo.photo.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Only the photo owner can delete the original'}), 403
    
    try:
        photo = vault_photo.photo
        
        # Check if photo is shared in multiple vaults or albums
        vault_shares_count = len(photo.vault_shares)
        has_album = photo.album_id is not None
        
        if vault_shares_count > 1 or has_album:
            return jsonify({
                'success': False, 
                'error': 'Photo is shared in multiple locations. Use "Remove from Vault" instead.',
                'conflicts': {
                    'vault_shares': vault_shares_count,
                    'in_album': has_album
                }
            }), 409
        
        # Delete the file
        file_deleted = delete_file_enhanced(photo.file_path)
        if photo.thumbnail_path:
            delete_file_enhanced(photo.thumbnail_path)
        if photo.edited_path:
            delete_file_enhanced(photo.edited_path)
        
        photo_name = photo.original_name
        
        # Delete from database (cascading will remove VaultPhoto)
        db.session.delete(photo)
        db.session.commit()
        
        logger.info(f"Photo {photo_name} deleted by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Photo "{photo_name}" deleted successfully',
            'file_deleted': file_deleted
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete photo: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete photo'}), 500