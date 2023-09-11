/**
 * Group User List
 */
 export interface GroupUser {
    name: string;
    unread?: string;
  }
  
  /**
   * Chat User List
   */
  export interface ChatUser {
    image?: string;
    name: string;
    status: string;
    unread?: string;
  }
  
  /**
   * Chat Message List
   */
  export interface ChatMessage {
    align?: string;
    name?: any;
    profile?: any;
    message?: string;
    time?: any;
    image?: string[];
    replayName?:any;
    replaymsg?:any;
  }

/**
 * Contact List
 */
 export interface ContactModel {
  title: string;
  contacts: Array<{
    name?: any;
    profile?: string;
  }>;
}
  