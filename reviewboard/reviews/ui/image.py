from __future__ import unicode_literals

from django.utils.html import escape
from djblets.util.templatetags.djblets_images import crop_image

from reviewboard.reviews.ui.base import FileAttachmentReviewUI
from reviewboard.site.urlresolvers import local_site_reverse


class ImageReviewUI(FileAttachmentReviewUI):
    name = 'Image'
    supported_mimetypes = ['image/*']

    allow_inline = True
    supports_diffing = True

    js_model_class = 'RB.ImageReviewable'
    js_view_class = 'RB.ImageReviewableView'

    def get_js_model_data(self):
        data = super(ImageReviewUI, self).get_js_model_data()
        data['imageURL'] = self.obj.file.url

        if self.diff_against_obj:
            data['diffAgainstImageURL'] = self.diff_against_obj.file.url

        return data

    def get_js_view_data(self):
        data = super(ImageReviewUI, self).get_js_view_data()
        self._append_view_navigation_data(data)
        return data

    def _append_view_navigation_data(self, data):
        """ Append information about previous and next image attachments on the
        review request.
        """
        found_current_attachment = False
        for attachment in self.review_request.get_file_attachments():
            if attachment.is_from_diff:
                continue

            # Only include other attachments that would have been viewed with this Review UI.
            if type(self) != type(FileAttachmentReviewUI.for_type(attachment)):
                continue

            # This is a valid attachment after we found the attachment being
            # reviewed therefore this is the "next" attachment and we break.
            if found_current_attachment:
                data['nextImageAttachment'] = {
                    'caption': attachment.caption,
                    'reviewURL': local_site_reverse('file-attachment',
                                                    args=[self.review_request.display_id,
                                                          attachment.pk]),
                }
                break

            # This is the attachment being reviewed so make note of this so we
            # can output the previous and next.
            if attachment == self.obj:
                found_current_attachment = True

            # We haven't found the attachment being reviewed so make note of
            # this one in case it's the one just before the one being reviewed.
            if not found_current_attachment:
                data['previousImageAttachment'] = {
                    'caption': attachment.caption,
                    'reviewURL': local_site_reverse('file-attachment',
                                                    args=[self.review_request.display_id,
                                                          attachment.pk]),
                }

    def serialize_comments(self, comments):
        result = {}
        serialized_comments = \
            super(ImageReviewUI, self).serialize_comments(comments)

        for serialized_comment in serialized_comments:
            try:
                position = '%(x)sx%(y)s+%(width)s+%(height)s' \
                           % serialized_comment
            except KeyError:
                # It's possible this comment was made before the review UI
                # was provided, meaning it has no data. If this is the case,
                # ignore this particular comment, since it doesn't have a
                # region.
                continue

            result.setdefault(position, []).append(serialized_comment)

        return result

    def get_comment_thumbnail(self, comment):
        try:
            x = int(comment.extra_data['x'])
            y = int(comment.extra_data['y'])
            width = int(comment.extra_data['width'])
            height = int(comment.extra_data['height'])
        except (KeyError, ValueError):
            # This may be a comment from before we had review UIs. Or,
            # corrupted data. Either way, don't display anything.
            return None

        image_url = crop_image(comment.file_attachment.file,
                               x, y, width, height)
        image_html = (
            '<img class="modified-image" src="%s" width="%s" height="%s" '
            'alt="%s" />'
            % (image_url, width, height, escape(comment.text)))

        if comment.diff_against_file_attachment_id:
            diff_against_image_url = crop_image(
                comment.diff_against_file_attachment.file,
                x, y, width, height)

            diff_against_image_html = (
                '<img class="orig-image" src="%s" width="%s" '
                'height="%s" alt="%s" />'
                % (diff_against_image_url, width, height,
                   escape(comment.text)))

            return ('<div class="image-review-ui-diff-thumbnail">%s%s</div>'
                    % (diff_against_image_html, image_html))
        else:
            return image_html
