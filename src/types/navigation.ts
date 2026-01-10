export type RootStackParamList = {
  Login: undefined;
  Register: undefined;
  MainApp: undefined;
};

export type MainTabParamList = {
  Dashboard: undefined;
  Accounting: undefined;
  Messages: undefined;
  Members: undefined;
  Meetings: undefined;
  Profile: undefined;
};

export type AccountingStackParamList = {
  AccountingList: undefined;
  AddTransaction: undefined;
  TransactionDetail: {transactionId: string};
};

export type MessagesStackParamList = {
  MessageList: undefined;
  ChatRoom: {roomId: string; roomName: string};
};

export type MeetingsStackParamList = {
  MeetingsList: undefined;
  MeetingDetails: {meetingId: number};
  CreateMeeting: undefined;
  MarkAttendance: {meetingId: number};
  RecordMinutes: {meetingId: number};
};

export type ResourceStackParamList = {
  ResourceCenterHome: undefined;
  TemplatesList: {category: string; categoryName: string};
  GenerateDocument: {template: any}; // Template type from resourceService
};
