# -*- coding: utf-8 -*-
from __future__ import with_statement
import Live
from _Framework.ControlSurface import ControlSurface


class LinkedClips (ControlSurface):
    u""" Rumotescripts LinkedClips """
    
    def __init__ (self, c_instance):
        ControlSurface.__init__ (self, c_instance)
        with self.component_guard ():
            self.arrangement_clips = set ()
            self.clip = self.song().view.detail_clip
            if self.clip:
                self.clip.add_name_listener (self._on_clip_name_changed)
                if self.clip.name:
                    self.add_named_clip_listeners ()
                    if self.clip.is_arrangement_clip:
                        self._copy_data_from_existing_clip ()
                        self.arrangement_clips.add (self.clip)
            self.song().view.add_detail_clip_listener (self._on_detail_clip_changed)
    
    def _on_detail_clip_changed (self):
        self.schedule_message (1, self._change_clip_listeners)
    def _change_clip_listeners (self):
        if self.clip and hasattr (self.clip, 'name'):  # left the clip, clip exists (not deleting)
            self.clip.remove_name_listener (self._on_clip_name_changed)
            if self.clip.name:
                self.remove_named_clip_listeners ()
                self._change_another_clips_nonlisteners ()
        ############################
        self.clip = self.song().view.detail_clip
        ############################
        if self.clip:
            self.clip.add_name_listener (self._on_clip_name_changed)
            if self.clip.name:
                self.add_named_clip_listeners ()
                if self.clip.is_arrangement_clip:
                    self._copy_data_from_existing_clip ()
                    self.arrangement_clips.add (self.clip)
    
    def add_named_clip_listeners (self):
        self._change_named_clip_listeners ('add')
    def remove_named_clip_listeners (self):
        self._change_named_clip_listeners ('remove')
    def _change_named_clip_listeners (self, action):
        if self.clip.color_has_listener (self._on_clip_color_changed) == (action == 'remove'):  # are there any listeners
            getattr (self.clip, action + '_looping_listener') (self._on_clip_looping_changed)
            getattr (self.clip, action + '_loop_start_listener') (self._on_clip_loop_start_changed)
            getattr (self.clip, action + '_loop_end_listener') (self._on_clip_loop_end_changed)
            getattr (self.clip, action + '_color_listener') (self._on_clip_color_changed)
            getattr (self.clip, action + '_signature_numerator_listener') (self._on_clip_signature_numerator_changed)
            getattr (self.clip, action + '_signature_denominator_listener') (self._on_clip_signature_denominator_changed)
            if self.clip.is_midi_clip:
                getattr (self.clip, action + '_notes_listener') (self._on_clip_notes_changed)
            else:  # if self.clip.is_audio_clip
                getattr (self.clip, action + '_gain_listener') (self._on_clip_gain_changed)
                getattr (self.clip, action + '_pitch_coarse_listener') (self._on_clip_pitch_coarse_changed)
                getattr (self.clip, action + '_pitch_fine_listener') (self._on_clip_pitch_fine_changed)
                getattr (self.clip, action + '_warping_listener') (self._on_clip_warping_changed)
                getattr (self.clip, action + '_warp_mode_listener') (self._on_clip_warp_mode_changed)
    
    def _on_clip_name_changed (self):
        self.schedule_message (1, self._clip_name_changed_actions)  # since it is not possible to change the clip inside the listener
    def _clip_name_changed_actions (self):
        with Undo ():
            self._change_another_clips_nonlisteners ()
            if self.clip.name:
                self.add_named_clip_listeners ()
                if self.clip.is_arrangement_clip:
                    self.arrangement_clips.add (self.clip)
                self._copy_data_from_existing_clip ()
            else:
                self.remove_named_clip_listeners ()
                if self.clip.is_arrangement_clip:
                    self.arrangement_clips.remove (self.clip)
    
    def _copy_data_from_existing_clip (self):
        try: clip = self.another_clips().next ()
        except StopIteration: return
        ####################################
        looping = clip.looping
        if clip.is_audio_clip: warping = clip.warping  # necessary, because when you turn on the loop the warping is automatically turned on
        self.clip.looping = clip.looping = True
        #self.clip.start_marker = clip.start_marker
        #self.clip.end_marker = clip.end_marker
        self.clip.loop_start = clip.loop_start
        self.clip.loop_end = clip.loop_end
        if not looping: self.clip.looping = clip.looping = False
        if clip.is_audio_clip: self.clip.warping = clip.warping = warping
        ##############################
        self.clip.color = clip.color
        self.clip.signature_numerator = clip.signature_numerator
        self.clip.signature_denominator = clip.signature_denominator
        self.clip.view.grid_quantization = clip.view.grid_quantization
        self.clip.view.grid_is_triplet = clip.view.grid_is_triplet
        ##############################
        if self.clip.is_midi_clip:
            notes = _get_all_notes (clip)
            if _get_all_notes (self.clip) != notes:
                _replace_notes (self.clip, notes)
        else:  # if self.clip.is_audio_clip
            self.clip.gain = clip.gain
            self.clip.pitch_coarse = clip.pitch_coarse
            self.clip.pitch_fine = clip.pitch_fine
            self.clip.warping = clip.warping = warping
            self.clip.warp_mode = clip.warp_mode
    
    def _change_another_clips_nonlisteners (self):
        def action_for_not_looped_clip (): pass
        if not self.clip.looping:
            if self.clip.is_audio_clip: warping = self.clip.warping  # necessary, because when you turn on the loop the warping is automatically turned on
            self.clip.looping = True
            loop_start = self.clip.loop_start
            loop_end = self.clip.loop_end
            self.clip.looping = False
            if self.clip.is_audio_clip: self.clip.warping = warping
            def copy_loop_startend ():
                clip.looping = True
                clip.loop_start = loop_start
                clip.loop_end = loop_end
                clip.looping = False
                if clip.is_audio_clip: clip.warping = warping
            action_for_not_looped_clip = copy_loop_startend
        ########################################
        for clip in self.another_clips ():
            action_for_not_looped_clip ()
            clip.view.grid_quantization = self.clip.view.grid_quantization
            clip.view.grid_is_triplet = self.clip.view.grid_is_triplet
    
    #################################################
    #################################################
    
    def _on_clip_looping_changed (self):
        self.schedule_message (1, self._change_another_clips_looping)
    def _change_another_clips_looping (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.looping = self.clip.looping
    
    def _on_clip_loop_start_changed (self):
        if self.clip.looping:
            self.schedule_message (1, self._change_another_clips_loop_start)
    def _change_another_clips_loop_start (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.loop_start = self.clip.loop_start
    
    def _on_clip_loop_end_changed (self):
        if self.clip.looping:
            self.schedule_message (1, self._change_another_clips_loop_end)
    def _change_another_clips_loop_end (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.loop_end = self.clip.loop_end
    
    def _on_clip_color_changed (self):
        self.schedule_message (1, self._change_another_clips_color)  # since it is not possible to change the clip inside the listener
    def _change_another_clips_color (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.color = self.clip.color
    
    def _on_clip_signature_numerator_changed (self):
        self.schedule_message (1, self._change_another_clips_signature_numerator)
    def _change_another_clips_signature_numerator (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.signature_numerator = self.clip.signature_numerator
    
    def _on_clip_signature_denominator_changed (self):
        self.schedule_message (1, self._change_another_clips_signature_denominator)
    def _change_another_clips_signature_denominator (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.signature_denominator = self.clip.signature_denominator
    
    def _on_clip_notes_changed (self):
        self.schedule_message (1, self._change_another_clips_notes)  # since it is not possible to change the clip inside the listener
    def _change_another_clips_notes (self):
        notes = _get_all_notes (self.clip)
        with Undo ():
            for clip in self.another_clips ():
                _replace_notes (clip, notes)
    
    def _on_clip_gain_changed (self):
        self.schedule_message (1, self._change_another_clips_gain)
    def _change_another_clips_gain (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.gain = self.clip.gain
    
    def _on_clip_pitch_coarse_changed (self):
        self.schedule_message (1, self._change_another_clips_pitch_coarse)
    def _change_another_clips_pitch_coarse (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.pitch_coarse = self.clip.pitch_coarse
    
    def _on_clip_pitch_fine_changed (self):
        self.schedule_message (1, self._change_another_clips_pitch_fine)
    def _change_another_clips_pitch_fine (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.pitch_fine = self.clip.pitch_fine
    
    def _on_clip_warping_changed (self):
        self.schedule_message (1, self._change_another_clips_warping)
    def _change_another_clips_warping (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.warping = self.clip.warping
    
    def _on_clip_warp_mode_changed (self):
        self.schedule_message (1, self._change_another_clips_warp_mode)
    def _change_another_clips_warp_mode (self):
        with Undo ():
            for clip in self.another_clips ():
                clip.warp_mode = self.clip.warp_mode
    
    #######################################################
    #######################################################
    
    def another_clips (self):
        """ Return an iterator over all clips of the same type (MIDI/audio), excluding the current one. """
        for track in self.song().tracks:
            if track.has_midi_input != self.clip.is_midi_clip: continue
            for clip_slot in track.clip_slots:
                if not clip_slot.has_clip: continue
                clip = clip_slot.clip
                if clip.name != self.clip.name: continue
                if self.clip.is_audio_clip and clip.file_path != self.clip.file_path:
                    clip.name += u'\''
                    continue
                if clip != self.clip:
                    yield clip
        self.arrangement_clips = set (filter (lambda clip: hasattr (clip, 'name'), self.arrangement_clips))  # only really existing clips
        for clip in self.arrangement_clips:
            if clip.name != self.clip.name or clip.is_midi_clip != self.clip.is_midi_clip: continue
            if self.clip.is_audio_clip and clip.file_path != self.clip.file_path:
                clip.name += u'\''
                continue
            if clip != self.clip:
                yield clip


def _get_all_notes (clip):
    assert isinstance (clip, Live.Clip.Clip)
    assert clip.is_midi_clip
    one_year_at_120bpm_in_beats = 63072000.0
    far_time = one_year_at_120bpm_in_beats
    return clip.get_notes (-far_time, 0, 2*far_time, 128)
def _replace_notes (clip, new_notes):
    assert isinstance (clip, Live.Clip.Clip)
    assert clip.is_midi_clip
    assert isinstance (new_notes, tuple)
    clip.select_all_notes ()
    clip.replace_selected_notes (new_notes)
    clip.deselect_all_notes ()


class Undo (object):
    def __enter__ (self):
        Live.Application.get_application().get_document().begin_undo_step ()
    def __exit__ (self, type, value, tb):
        Live.Application.get_application().get_document().end_undo_step ()
