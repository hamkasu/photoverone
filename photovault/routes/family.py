# photovault/routes/family.py

import logging
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
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

# Configure logging
logger = logging.getLogger(__name__)

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
    
    # Get user's role in vault
    user_role = vault.get_member_role(current_user.id)
    
    return render_template('family/vault_detail.html',
                         vault=vault,
                         vault_photos=vault_photos,
                         stories=stories,
                         members=members,
                         user_role=user_role)

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
            flash(f'Invitation sent to {email}', 'success')
            return redirect(url_for('family.view_vault', vault_id=vault_id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to send invitation: {str(e)}")
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