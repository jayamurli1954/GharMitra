/**
 * Meeting Management Service
 * Handles meeting creation, attendance, minutes, and resolutions
 */
import api from './api';

export type MeetingType = 'MC' | 'AGM' | 'EGM' | 'SGM' | 'committee' | 'general_body';
export type MeetingStatus = 'scheduled' | 'completed' | 'cancelled';
export type AttendanceStatus = 'present' | 'proxy' | 'absent';
export type ResolutionType = 'ordinary' | 'special' | 'unanimous';
export type ResolutionResult = 'passed' | 'rejected' | 'withdrawn';

export interface AgendaItemCreate {
  item_number: number;
  item_title: string;
  item_description?: string;
}

export interface MeetingCreate {
  meeting_type: MeetingType;
  meeting_date: string; // ISO date string
  meeting_time?: string;
  meeting_title: string;
  venue?: string;
  agenda_items?: AgendaItemCreate[];
  notice_sent_to?: 'all_members' | 'mc_only';
  // Legacy fields
  agenda?: string;
  attendees_count?: number;
  chaired_by?: string;
}

export interface MeetingUpdate {
  meeting_date?: string;
  meeting_time?: string;
  meeting_title?: string;
  venue?: string;
  status?: MeetingStatus;
  agenda?: string;
  attendees_count?: number;
  chaired_by?: string;
}

export interface Meeting {
  id: number;
  society_id: number;
  meeting_type: string;
  meeting_number?: string;
  meeting_date: string;
  meeting_time?: string;
  meeting_title: string;
  venue?: string;
  status: string;
  total_members_eligible?: number;
  total_members_present: number;
  quorum_required?: number;
  quorum_met: boolean;
  minutes_text?: string;
  minutes_approved: boolean;
  minutes_approved_date?: string;
  recorded_by?: string;
  recorded_at?: string;
  notice_sent: boolean;
  notice_sent_at?: string;
  notice_sent_to?: string;
  notice_sent_by?: number;
  notice_sent_by_name?: string;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  // Legacy fields
  agenda?: string;
  attendees_count?: number;
  chaired_by?: string;
}

export interface AgendaItem {
  id: number;
  item_number: number;
  item_title: string;
  item_description?: string;
  discussion_summary?: string;
  status: string;
  resolution_id?: number;
  created_at: string;
}

export interface AttendanceRecord {
  member_id: number;
  status: AttendanceStatus;
  proxy_holder_id?: number;
  arrival_time?: string;
  departure_time?: string;
}

export interface MarkAttendanceRequest {
  attendees: AttendanceRecord[];
}

export interface Attendance {
  id: number;
  member_id: number;
  member_name: string;
  member_flat?: string;
  status: string;
  proxy_holder_id?: number;
  proxy_holder_name?: string;
  arrival_time?: string;
  departure_time?: string;
  created_at: string;
}

export interface RecordMinutesRequest {
  minutes_text: string;
  agenda_updates?: Array<{
    agenda_item_id: number;
    discussion_summary?: string;
    status?: string;
  }>;
}

export interface CreateResolutionRequest {
  resolution_title: string;
  resolution_text: string;
  resolution_type: ResolutionType;
  proposed_by_id: number;
  seconded_by_id: number;
  votes_for: number;
  votes_against: number;
  votes_abstain: number;
  result: ResolutionResult;
  action_items?: string;
  assigned_to?: string;
  due_date?: string;
}

export interface Resolution {
  id: number;
  resolution_number: string;
  resolution_type?: string;
  resolution_title: string;
  resolution_text: string;
  proposed_by_id?: number;
  proposed_by_name: string;
  seconded_by_id?: number;
  seconded_by_name: string;
  votes_for: number;
  votes_against: number;
  votes_abstain: number;
  result: string;
  action_items?: string;
  assigned_to?: string;
  due_date?: string;
  implementation_status: string;
  created_at: string;
}

export interface MeetingDetails {
  meeting: Meeting;
  agenda_items: AgendaItem[];
  attendance: Attendance[];
  resolutions: Resolution[];
}

export interface MeetingNoticeRequest {
  send_email: boolean;
  send_sms?: boolean;
  custom_message?: string;
}

export interface MeetingNoticeResponse {
  meeting_id: number;
  notice_sent: boolean;
  recipients_count: number;
  recipients: Array<{
    id: string;
    name: string;
    email?: string;
    phone?: string;
    [key: string]: any;
  }>;
  sent_at: string;
  message: string;
}

export interface Member {
  id: number;
  name: string;
  flat_number?: string;
  email?: string;
  phone_number?: string;
}

export const meetingService = {
  // ===== List Meetings =====
  async getMeetings(params?: {
    meeting_type?: MeetingType;
    from_date?: string;
    to_date?: string;
  }): Promise<Meeting[]> {
    const response = await api.get<Meeting[]>('/meetings', { params });
    return response.data;
  },

  // ===== Get Single Meeting =====
  async getMeeting(meetingId: number): Promise<Meeting> {
    const response = await api.get<Meeting>(`/meetings/${meetingId}`);
    return response.data;
  },

  // ===== Get Complete Meeting Details =====
  async getMeetingDetails(meetingId: number): Promise<MeetingDetails> {
    const response = await api.get<MeetingDetails>(`/meetings/${meetingId}/details`);
    return response.data;
  },

  // ===== Create Meeting =====
  async createMeeting(data: MeetingCreate): Promise<Meeting> {
    const response = await api.post<Meeting>('/meetings', data);
    return response.data;
  },

  // ===== Update Meeting =====
  async updateMeeting(meetingId: number, data: MeetingUpdate): Promise<Meeting> {
    const response = await api.patch<Meeting>(`/meetings/${meetingId}`, data);
    return response.data;
  },

  // ===== Delete Meeting =====
  async deleteMeeting(meetingId: number): Promise<void> {
    await api.delete(`/meetings/${meetingId}`);
  },

  // ===== Mark Attendance =====
  async markAttendance(meetingId: number, data: MarkAttendanceRequest): Promise<Attendance[]> {
    const response = await api.post<Attendance[]>(`/meetings/${meetingId}/attendance`, data);
    return response.data;
  },

  // ===== Record Minutes =====
  async recordMinutes(meetingId: number, data: RecordMinutesRequest): Promise<Meeting> {
    const response = await api.post<Meeting>(`/meetings/${meetingId}/minutes`, data);
    return response.data;
  },

  // ===== Create Resolution =====
  async createResolution(meetingId: number, data: CreateResolutionRequest): Promise<Resolution> {
    const response = await api.post<Resolution>(`/meetings/${meetingId}/resolutions`, data);
    return response.data;
  },

  // ===== Send Meeting Notice =====
  async sendNotice(meetingId: number, data: MeetingNoticeRequest): Promise<MeetingNoticeResponse> {
    const response = await api.post<MeetingNoticeResponse>(
      `/meetings/${meetingId}/send-notice`,
      data,
    );
    return response.data;
  },

  // ===== Get Members (for attendance and resolutions) =====
  // Note: This should use usersService.getUsers() in the screens
  // Keeping this for backward compatibility but it's better to use usersService directly
  async getMembers(): Promise<Member[]> {
    try {
      const response = await api.get<any[]>('/users');
      return response.data.map(user => ({
        id: user.id,
        name: user.name,
        flat_number: user.apartment_number,
        email: user.email,
        phone_number: user.phone_number,
      }));
    } catch (error) {
      console.error('Error loading members:', error);
      return [];
    }
  },
};

