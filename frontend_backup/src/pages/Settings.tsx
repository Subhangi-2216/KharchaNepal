import React, { useState, useEffect, useRef, ChangeEvent, FormEvent } from 'react';
import { useAuth } from '@/contexts/AuthContext'; // Assuming context provides token, user info, loading state
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "sonner"; // Or your preferred toast library
import { Skeleton } from '@/components/ui/skeleton';
import { EmailProcessing } from '@/components/EmailProcessing';
import { TransactionApprovals } from '@/components/TransactionApprovals';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// --- Configuration ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// --- Helper Functions ---
const getInitials = (name?: string | null): string => {
  // Handle potential null or empty string
  return name ? name.charAt(0).toUpperCase() : '?';
};

// --- Component ---
export default function SettingsPage() {
  const { token, isLoading: isAuthLoading, isAuthenticated } = useAuth(); // Assuming context provides these

  // Profile State
  const [initialName, setInitialName] = useState<string | null>(null);
  const [initialEmail, setInitialEmail] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [profileImageUrl, setProfileImageUrl] = useState<string | null>(null); // Relative URL from backend
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null); // For local preview / fetched image URL
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Password State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');

  // Loading/Error State
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // --- OAuth Callback Handling ---
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const oauthSuccess = urlParams.get('oauth_success');
    const oauthError = urlParams.get('oauth_error');
    const email = urlParams.get('email');

    if (oauthSuccess === 'true') {
      // Show success message
      const message = email ? `Gmail account ${email} connected successfully!` : 'Gmail account connected successfully!';
      // You can add a toast notification here
      console.log(message);
      
      // Clean up URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Refresh the email accounts list if the EmailProcessing component is visible
      window.dispatchEvent(new CustomEvent('refreshEmailAccounts'));
    } else if (oauthError) {
      // Show error message
      const errorMessage = `Failed to connect Gmail account: ${oauthError}`;
      console.error(errorMessage);
      
      // Clean up URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // --- Effects ---
  // Fetch profile on load
  useEffect(() => {
    if (!isAuthLoading && isAuthenticated && token) {
      setIsLoadingProfile(true);
      setProfileError(null);
      fetch(`${API_BASE_URL}/api/user/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(async res => {
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: `Failed to fetch profile (${res.status})` }));
                throw new Error(errorData.detail || `Failed to fetch profile (${res.status})`);
            }
            return res.json();
        })
        .then(data => {
          const fetchedName = data.name || '';
          const fetchedEmail = data.email || '';
          const fetchedImageUrl = data.profile_image_url || null;

          setName(fetchedName);
          setEmail(fetchedEmail);
          setInitialName(fetchedName); // Store initial values
          setInitialEmail(fetchedEmail); // Store initial values
          setProfileImageUrl(fetchedImageUrl);
          // Construct full URL for display if relative URL exists
          setImagePreviewUrl(fetchedImageUrl ? `${API_BASE_URL}${fetchedImageUrl}` : null);
        })
        .catch(err => {
            console.error("Fetch profile error:", err);
            const errorMsg = err.message || "Could not load profile.";
            setProfileError(errorMsg);
            toast.error(errorMsg);
        })
        .finally(() => setIsLoadingProfile(false));
    } else if (!isAuthLoading && !isAuthenticated) {
        // Handle case where user is definitely not logged in
        setIsLoadingProfile(false);
        setProfileError("Please log in to view settings.");
    }
  }, [token, isAuthLoading, isAuthenticated]); // Re-fetch if auth state changes

  // Cleanup object URL for image preview
  useEffect(() => {
      // Revoke the object URL when the component unmounts or the preview URL changes
      let currentPreview = imagePreviewUrl;
      return () => {
          if (currentPreview && currentPreview.startsWith('blob:')) {
              URL.revokeObjectURL(currentPreview);
          }
      };
  }, [imagePreviewUrl]);


  // --- Handlers ---
  const handleImageChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      // Basic frontend type check
      const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
          toast.error("Invalid file type. Please select a JPG, PNG, or WEBP image.");
          event.target.value = ''; // Reset file input
          return;
      }
      // Basic frontend size check (backend enforces stricter limit)
      if (file.size > 2 * 1024 * 1024) { // ~2MB
           toast.error("File is too large. Maximum size is 2MB.");
           event.target.value = ''; // Reset file input
           return;
       }

      setSelectedImageFile(file);
      // Revoke previous blob URL if exists
      if (imagePreviewUrl && imagePreviewUrl.startsWith('blob:')) {
          URL.revokeObjectURL(imagePreviewUrl);
      }
      // Create new object URL for preview
      setImagePreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleProfileSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || isUpdatingProfile || isUploadingImage) return;

    let updatedProfileImageUrl = profileImageUrl; // Start with existing or null
    const profileUpdatePayload: { name?: string | null; email?: string } = {};
    let needsProfileUpdate = false;

    // Check if name or email changed
    if (name !== initialName) {
        profileUpdatePayload.name = name.trim() === '' ? null : name.trim(); // Send null if empty, else trimmed name
        needsProfileUpdate = true;
    }
    if (email !== initialEmail) {
        profileUpdatePayload.email = email;
        needsProfileUpdate = true;
    }

    setIsUpdatingProfile(true); // General saving state
    setProfileError(null);

    try {
        // 1. Upload Image if selected
        if (selectedImageFile) {
            setIsUploadingImage(true); // Specific state for upload
            const formData = new FormData();
            formData.append("file", selectedImageFile);

            const imgResponse = await fetch(`${API_BASE_URL}/api/user/profile/image`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }, // Content-Type is set by FormData
                body: formData,
            });

            setIsUploadingImage(false); // Finished upload attempt

            if (!imgResponse.ok) {
                const errorData = await imgResponse.json().catch(() => ({ detail: 'Image upload failed.' }));
                throw new Error(errorData.detail || `Image upload failed (${imgResponse.status})`);
            }
            const imgData = await imgResponse.json();
            updatedProfileImageUrl = imgData.profile_image_url; // Get relative URL from backend
            setProfileImageUrl(updatedProfileImageUrl); // Update state
            setSelectedImageFile(null); // Clear selected file
            // Update preview to the new URL (or keep local blob if backend didn't return one?)
             setImagePreviewUrl(updatedProfileImageUrl ? `${API_BASE_URL}${updatedProfileImageUrl}` : null);
            toast.success("Profile image updated!");
            needsProfileUpdate = true; // Mark for profile update even if only image changed (to potentially refresh UI/context)
        }

        // 2. Update Name/Email if changed (or maybe always if image changed?)
        // Send PUT request only if name/email changed OR if an image was just uploaded successfully
        if (needsProfileUpdate && Object.keys(profileUpdatePayload).length > 0) {
            const profileResponse = await fetch(`${API_BASE_URL}/api/user/profile`, {
                method: 'PUT',
                headers: {
                     'Authorization': `Bearer ${token}`,
                     'Content-Type': 'application/json'
                },
                body: JSON.stringify(profileUpdatePayload),
            });

            if (!profileResponse.ok) {
                const errorData = await profileResponse.json().catch(() => ({ detail: 'Profile update failed.' }));
                throw new Error(errorData.detail || `Profile update failed (${profileResponse.status})`);
            }

            const updatedProfile = await profileResponse.json();
            // Update state & initial values after successful update
            const newName = updatedProfile.name || '';
            const newEmail = updatedProfile.email || '';
            setName(newName);
            setEmail(newEmail);
            setInitialName(newName); // Update baseline
            setInitialEmail(newEmail); // Update baseline
            toast.success("Profile details updated!");
        } else if (selectedImageFile && !needsProfileUpdate) {
            // Only image was updated, no other profile changes needed
            // toast.success("Profile image updated!"); // Already toasted above
        } else if (!selectedImageFile && !needsProfileUpdate) {
            toast.info("No changes detected in profile information.");
        }

    } catch (err: any) {
      console.error("Profile update error:", err);
      const errorMsg = err.message || "Failed to update profile.";
      setProfileError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsUpdatingProfile(false);
      setIsUploadingImage(false); // Ensure reset
      // Clear file input value in case the same file needs to be selected again after an error
      if (fileInputRef.current) {
          fileInputRef.current.value = '';
      }
    }
  };


  const handlePasswordSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || isUpdatingPassword) return;
    setPasswordError(null); // Clear previous errors

    // Frontend validation matching backend schema
    if (newPassword !== confirmNewPassword) {
        setPasswordError("New passwords do not match.");
        toast.error("New passwords do not match.");
        return;
    }
    if (newPassword.length < 8) {
         setPasswordError("New password must be at least 8 characters long.");
         toast.error("New password must be at least 8 characters long.");
         return;
     }

    setIsUpdatingPassword(true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/user/password`, {
            method: 'PUT',
            headers: {
                 'Authorization': `Bearer ${token}`,
                 'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_new_password: confirmNewPassword
            }),
        });

         if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Password update failed.' }));
            throw new Error(errorData.detail || `Password update failed (${response.status})`);
        }

        toast.success("Password updated successfully!");
        // Clear password fields after success
        setCurrentPassword('');
        setNewPassword('');
        setConfirmNewPassword('');

    } catch (err: any) {
       console.error("Password update error:", err);
       const errorMsg = err.message || "Failed to update password.";
       setPasswordError(errorMsg);
       toast.error(errorMsg);
    } finally {
        setIsUpdatingPassword(false);
    }
  };

  // --- Render Logic ---
  // Show main loading skeleton if auth is loading or initial profile fetch is happening
  if (isAuthLoading || isLoadingProfile) {
       return (
         <div className="space-y-6 p-4 md:p-6 animate-pulse">
             <Skeleton className="h-8 w-1/4" />
             <Skeleton className="h-6 w-1/3 mb-6" />
             <Card><CardContent className="p-6"><Skeleton className="h-64 w-full" /></CardContent></Card>
             <Card><CardContent className="p-6"><Skeleton className="h-64 w-full" /></CardContent></Card>
         </div>
       );
   }

   // Handle case where user is not authenticated after loading finishes
   if (!isAuthenticated) {
       return (
            <div className="p-6 text-center">
                <p className="text-lg text-destructive">{profileError || "Please log in to access settings."}</p>
                {/* Optionally add a link to login */}
            </div>
        );
   }

  // Main component render
  return (
    <div className="space-y-8 p-4 md:p-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Manage your account settings, profile, and automated expense tracking.</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="password">Password</TabsTrigger>
          <TabsTrigger value="email-processing">Email Processing</TabsTrigger>
          <TabsTrigger value="approvals">Transaction Approvals</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
      
        {/* --- Profile Settings Card --- */}
        <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
          <CardDescription>Update your personal details and profile picture.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProfileSubmit} className="space-y-6">
             {/* Profile Picture */}
             <div className="flex flex-col items-center space-y-4">
                 <Avatar className="h-24 w-24 cursor-pointer ring-offset-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2" onClick={handleAvatarClick} tabIndex={0}>
                     <AvatarImage src={imagePreviewUrl ?? undefined} alt={name || 'User Profile'} />
                     <AvatarFallback>{getInitials(name)}</AvatarFallback>
                 </Avatar>
                 <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleImageChange}
                    accept="image/png, image/jpeg, image/webp" // Match backend ALLOWED_IMAGE_EXTENSIONS
                    style={{ display: 'none' }} // Hide the default input
                    aria-hidden="true"
                 />
                 <Button type="button" variant="outline" size="sm" onClick={handleAvatarClick} disabled={isUploadingImage || isUpdatingProfile}>
                     {isUploadingImage ? 'Uploading...' : 'Change Picture'}
                 </Button>
                 {selectedImageFile && !isUploadingImage && <p className="text-xs text-muted-foreground">Previewing: {selectedImageFile.name}</p>}
                 {profileError && <p className="text-sm text-destructive">{profileError}</p>}
             </div>

             <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                 {/* Name */}
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your full name"
                    disabled={isUpdatingProfile}
                  />
              </div>
                {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    required // Email is usually required
                    disabled={isUpdatingProfile}
                  />
              </div>
            </div>
            
             {/* Save Button */}
             <div className="flex justify-end">
                <Button type="submit" disabled={isUpdatingProfile || isUploadingImage}>
                    {(isUpdatingProfile || isUploadingImage) ? 'Saving...' : 'Save Profile Changes'}
                </Button>
             </div>
          </form>
        </CardContent>
        </Card>
        </TabsContent>

        <TabsContent value="password" className="space-y-6">
        {/* --- Change Password Card --- */}
        <Card>
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
          <CardDescription>Update your account password securely.</CardDescription>
        </CardHeader>
        <CardContent>
           <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div className="space-y-2">
               <Label htmlFor="currentPassword">Current Password</Label>
               <Input
                 id="currentPassword"
                 type="password"
                 value={currentPassword}
                 onChange={(e) => setCurrentPassword(e.target.value)}
                 required
                 autoComplete="current-password"
                 disabled={isUpdatingPassword}
               />
              </div>
              <div className="space-y-2">
               <Label htmlFor="newPassword">New Password</Label>
               <Input
                 id="newPassword"
                 type="password"
                 value={newPassword}
                 onChange={(e) => setNewPassword(e.target.value)}
                 required
                 minLength={8}
                 autoComplete="new-password"
                 disabled={isUpdatingPassword}
               />
                <p className="text-xs text-muted-foreground">Minimum 8 characters.</p>
              </div>
              <div className="space-y-2">
               <Label htmlFor="confirmNewPassword">Confirm New Password</Label>
               <Input
                 id="confirmNewPassword"
                 type="password"
                 value={confirmNewPassword}
                 onChange={(e) => setConfirmNewPassword(e.target.value)}
                 required
                 minLength={8}
                 autoComplete="new-password"
                 disabled={isUpdatingPassword}
               />
              </div>
              {passwordError && <p className="text-sm text-destructive">{passwordError}</p>}
             <div className="flex justify-end">
                <Button type="submit" disabled={isUpdatingPassword}>
                    {isUpdatingPassword ? 'Updating...' : 'Update Password'}
                </Button>
            </div>
           </form>
          </CardContent>
        </Card>
        </TabsContent>

        <TabsContent value="email-processing" className="space-y-6">
          <EmailProcessing />
        </TabsContent>

        <TabsContent value="approvals" className="space-y-6">
          <TransactionApprovals />
        </TabsContent>
      </Tabs>
    </div>
  );
}
