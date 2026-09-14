# App Review Notes

PickerRoy processes user-selected video files entirely on the device. It has no account system, network service, analytics SDK, advertising SDK, subscription, or in-app purchase.

Testing flow:

1. Tap Import Video and select a local video.
2. Choose an aspect ratio.
3. Tap Start Analysis.
4. Pause, resume, or cancel from the analysis controls if desired.
5. Select recommended frames and use Like or Show Less to update the local preference profile.
6. Export selected frames directly or with optional enhancement.

All user-selected files are accessed through system file pickers. The macOS build uses App Sandbox with user-selected read/write access. Video content and preference data are never uploaded.

No login or review account is required.

