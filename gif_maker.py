import os
import io
import threading
import customtkinter as ctk
from PIL import Image, ImageTk, ImageChops, ImageOps
import requests
from tkinter import filedialog, messagebox
from urllib.parse import urlparse
import math

class GifMakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Maker")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # Variables
        self.images = []
        self.image_paths = []
        self.image_animations = []  # Store animation type for each image
        self.preview_image = None
        self.current_preview_index = 0
        
        # Animation options
        self.animation_types = [
            "None", "Instant", "Fade in", 
            "Slide up", "Slide down", "Slide right", 
            "Slide left", "Grow", "Shrink"
        ]
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create Header
        self.header_label = ctk.CTkLabel(
            self.main_frame, 
            text="GIF Maker", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.header_label.pack(pady=10)
        
        # Create content frame with two columns
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left column (controls)
        self.controls_frame = ctk.CTkFrame(self.content_frame, width=300)
        self.controls_frame.pack(side="left", fill="both", padx=5, pady=5, expand=False)
        
        # Image source section
        self.source_label = ctk.CTkLabel(
            self.controls_frame, 
            text="Image Source", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.source_label.pack(pady=(10, 5), anchor="w", padx=10)
        
        # URL option
        self.url_frame = ctk.CTkFrame(self.controls_frame)
        self.url_frame.pack(fill="x", padx=10, pady=5)
        
        self.url_label = ctk.CTkLabel(self.url_frame, text="Image URL:")
        self.url_label.pack(anchor="w")
        
        self.url_entry = ctk.CTkEntry(self.url_frame, width=200)
        self.url_entry.pack(fill="x", pady=(0, 5))
        
        self.fetch_button = ctk.CTkButton(
            self.url_frame, 
            text="Fetch Image", 
            command=self.fetch_image
        )
        self.fetch_button.pack(fill="x")
        
        # Local file option
        self.file_frame = ctk.CTkFrame(self.controls_frame)
        self.file_frame.pack(fill="x", padx=10, pady=10)
        
        self.file_label = ctk.CTkLabel(self.file_frame, text="Local Images:")
        self.file_label.pack(anchor="w")
        
        self.browse_button = ctk.CTkButton(
            self.file_frame, 
            text="Browse Files", 
            command=self.browse_files
        )
        self.browse_button.pack(fill="x", pady=5)
        
        # Animation settings
        self.animation_label = ctk.CTkLabel(
            self.controls_frame, 
            text="Animation Settings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.animation_label.pack(pady=(15, 5), anchor="w", padx=10)
        
        self.animation_frame = ctk.CTkFrame(self.controls_frame)
        self.animation_frame.pack(fill="x", padx=10, pady=5)
        
        self.animation_type_label = ctk.CTkLabel(self.animation_frame, text="Transition Type:")
        self.animation_type_label.pack(anchor="w", pady=(5, 0))
        
        # Animation/transition selection
        self.animation_var = ctk.StringVar(value=self.animation_types[0])
        self.animation_dropdown = ctk.CTkOptionMenu(
            self.animation_frame,
            values=self.animation_types,
            variable=self.animation_var,
            command=self.animation_selected
        )
        self.animation_dropdown.pack(fill="x", pady=5)
        
        # Apply animation button
        self.apply_animation_button = ctk.CTkButton(
            self.animation_frame,
            text="Apply to Selected Image",
            command=self.apply_animation_to_selected
        )
        self.apply_animation_button.pack(fill="x", pady=5)
        
        # Apply to all button
        self.apply_all_button = ctk.CTkButton(
            self.animation_frame,
            text="Apply to All Images",
            command=self.apply_animation_to_all
        )
        self.apply_all_button.pack(fill="x", pady=5)
        
        # GIF settings
        self.settings_label = ctk.CTkLabel(
            self.controls_frame, 
            text="GIF Settings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.settings_label.pack(pady=(15, 5), anchor="w", padx=10)
        
        self.settings_frame = ctk.CTkFrame(self.controls_frame)
        self.settings_frame.pack(fill="x", padx=10, pady=5)
        
        self.duration_label = ctk.CTkLabel(self.settings_frame, text="Frame Duration (ms):")
        self.duration_label.pack(anchor="w", pady=(5, 0))
        
        self.duration_entry = ctk.CTkEntry(self.settings_frame)
        self.duration_entry.pack(fill="x", pady=5)
        self.duration_entry.insert(0, "200")
        
        self.loop_label = ctk.CTkLabel(self.settings_frame, text="Loop Count (0 = infinite):")
        self.loop_label.pack(anchor="w", pady=(5, 0))
        
        self.loop_entry = ctk.CTkEntry(self.settings_frame)
        self.loop_entry.pack(fill="x", pady=5)
        self.loop_entry.insert(0, "0")
        
        # Transition frames
        self.frames_label = ctk.CTkLabel(self.settings_frame, text="Transition Frames:")
        self.frames_label.pack(anchor="w", pady=(5, 0))
        
        self.frames_entry = ctk.CTkEntry(self.settings_frame)
        self.frames_entry.pack(fill="x", pady=5)
        self.frames_entry.insert(0, "10")
        
        # Create GIF button
        self.create_gif_button = ctk.CTkButton(
            self.controls_frame, 
            text="Create GIF", 
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            command=self.create_gif
        )
        self.create_gif_button.pack(fill="x", padx=10, pady=20)
        
        # Status label
        self.status_label = ctk.CTkLabel(self.controls_frame, text="Status: Ready")
        self.status_label.pack(fill="x", padx=10, pady=5)
        
        # Right column (preview)
        self.preview_frame = ctk.CTkFrame(self.content_frame)
        self.preview_frame.pack(side="right", fill="both", padx=5, pady=5, expand=True)
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame, 
            text="Image Preview", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.preview_label.pack(pady=10)
        
        # Image preview
        self.image_display = ctk.CTkLabel(self.preview_frame, text="No images loaded")
        self.image_display.pack(expand=True)
        
        # Navigation buttons for preview
        self.nav_frame = ctk.CTkFrame(self.preview_frame)
        self.nav_frame.pack(fill="x", padx=10, pady=10)
        
        self.prev_button = ctk.CTkButton(
            self.nav_frame, 
            text="Previous", 
            command=self.show_previous_image,
            width=120
        )
        self.prev_button.pack(side="left", padx=5)
        
        self.next_button = ctk.CTkButton(
            self.nav_frame, 
            text="Next", 
            command=self.show_next_image,
            width=120
        )
        self.next_button.pack(side="right", padx=5)
        
        self.image_counter = ctk.CTkLabel(self.nav_frame, text="0/0")
        self.image_counter.pack(side="left", expand=True)
        
        # Image list display
        self.image_list_frame = ctk.CTkFrame(self.preview_frame)
        self.image_list_frame.pack(fill="x", padx=10, pady=10)
        
        self.image_list_label = ctk.CTkLabel(
            self.image_list_frame, 
            text="Added Images:", 
            font=ctk.CTkFont(weight="bold")
        )
        self.image_list_label.pack(anchor="w", pady=5)
        
        self.image_list = ctk.CTkTextbox(self.image_list_frame, height=100)
        self.image_list.pack(fill="x")
        self.image_list.configure(state="disabled")
        
        # Remove selected image button
        self.remove_button = ctk.CTkButton(
            self.image_list_frame, 
            text="Remove Selected", 
            command=self.remove_selected_image
        )
        self.remove_button.pack(pady=5, anchor="e")
        
        # Update UI state
        self.update_ui_state()
    
    def animation_selected(self, choice):
        # This function is called when an animation type is selected
        pass
    
    def apply_animation_to_selected(self):
        if not self.images or self.current_preview_index >= len(self.images):
            messagebox.showerror("Error", "No image selected")
            return
        
        # Get the selected animation type
        animation_type = self.animation_var.get()
        
        # Update the animation type for the selected image
        # Make sure image_animations has at least as many elements as images
        while len(self.image_animations) < len(self.images):
            self.image_animations.append("None")
        
        self.image_animations[self.current_preview_index] = animation_type
        
        # Update the image list to show the animation type
        self.update_image_list()
        
        self.status_label.configure(text=f"Status: Applied '{animation_type}' to image {self.current_preview_index + 1}")
    
    def apply_animation_to_all(self):
        if not self.images:
            messagebox.showerror("Error", "No images loaded")
            return
        
        # Get the selected animation type
        animation_type = self.animation_var.get()
        
        # Apply to all images
        self.image_animations = [animation_type] * len(self.images)
        
        # Update the image list to show the animation types
        self.update_image_list()
        
        self.status_label.configure(text=f"Status: Applied '{animation_type}' to all images")
    
    def update_image_list(self):
        # Update the image list display with animation types
        self.image_list.configure(state="normal")
        self.image_list.delete("1.0", "end")
        
        for i, path in enumerate(self.image_paths):
            animation = self.image_animations[i] if i < len(self.image_animations) else "None"
            self.image_list.insert("end", f"{i+1}. {os.path.basename(path)} [{animation}]\n")
        
        self.image_list.configure(state="disabled")
    
    def fetch_image(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        # Check if URL is valid
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                messagebox.showerror("Error", "Invalid URL format")
                return
        except Exception:
            messagebox.showerror("Error", "Invalid URL format")
            return
        
        self.status_label.configure(text="Status: Fetching image...")
        
        # Run in a thread to avoid freezing UI
        threading.Thread(target=self._fetch_image_thread, args=(url,), daemon=True).start()
    
    def _fetch_image_thread(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Check if it's an image
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                self.root.after(0, lambda: messagebox.showerror("Error", f"URL does not point to an image: {content_type}"))
                self.root.after(0, lambda: self.status_label.configure(text="Status: Error fetching image"))
                return
            
            # Generate a filename from URL
            filename = os.path.basename(urlparse(url).path)
            if not filename or '.' not in filename:
                filename = f"image_{len(self.images)}.jpg"
            
            # Save path
            save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gif_maker", "images")
            os.makedirs(save_dir, exist_ok=True)
            
            full_path = os.path.join(save_dir, filename)
            
            # Save the image
            with open(full_path, 'wb') as f:
                f.write(response.content)
            
            # Add to our list
            image = Image.open(io.BytesIO(response.content))
            
            self.root.after(0, lambda: self._add_image(image, full_path))
            self.root.after(0, lambda: self.status_label.configure(text=f"Status: Image saved to {filename}"))
            
        except requests.RequestException as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch image: {str(e)}"))
            self.root.after(0, lambda: self.status_label.configure(text="Status: Error fetching image"))
    
    def browse_files(self):
        filetypes = (
            ('Image files', '*.png *.jpg *.jpeg *.gif *.bmp *.tiff'),
            ('All files', '*.*')
        )
        
        filenames = filedialog.askopenfilenames(
            title='Select Images',
            initialdir=os.path.expanduser("~"),
            filetypes=filetypes
        )
        
        if not filenames:
            return
        
        for filename in filenames:
            try:
                image = Image.open(filename)
                self._add_image(image, filename)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open {os.path.basename(filename)}: {str(e)}")
    
    def _add_image(self, image, path):
        self.images.append(image)
        self.image_paths.append(path)
        self.image_animations.append("None")  # Default animation
        
        # Update the image list display
        self.update_image_list()
        
        # Show the newly added image
        self.current_preview_index = len(self.images) - 1
        self.update_preview()
        self.update_ui_state()
    
    def update_preview(self):
        if not self.images:
            self.image_display.configure(text="No images loaded")
            self.image_counter.configure(text="0/0")
            return
        
        # Get the current image
        image = self.images[self.current_preview_index]
        
        # Resize for preview if needed
        max_size = (400, 400)
        image = self.resize_image_for_preview(image, max_size)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(image)
        
        # Store reference to prevent garbage collection
        self.preview_image = photo
        
        # Update the display
        self.image_display.configure(text="")
        self.image_display.configure(image=photo)
        
        # Update counter
        self.image_counter.configure(text=f"{self.current_preview_index + 1}/{len(self.images)}")
        
        # Update animation selection to match the current image
        if self.current_preview_index < len(self.image_animations):
            self.animation_var.set(self.image_animations[self.current_preview_index])
    
    def resize_image_for_preview(self, image, max_size):
        width, height = image.size
        
        # Calculate the new size
        if width > max_size[0] or height > max_size[1]:
            ratio = min(max_size[0] / width, max_size[1] / height)
            new_size = (int(width * ratio), int(height * ratio))
            return image.resize(new_size, Image.LANCZOS)
        
        return image
    
    def show_next_image(self):
        if not self.images:
            return
        
        self.current_preview_index = (self.current_preview_index + 1) % len(self.images)
        self.update_preview()
    
    def show_previous_image(self):
        if not self.images:
            return
        
        self.current_preview_index = (self.current_preview_index - 1) % len(self.images)
        self.update_preview()
    
    def remove_selected_image(self):
        if not self.images or self.current_preview_index >= len(self.images):
            return
        
        # Remove the image and its animation
        del self.images[self.current_preview_index]
        del self.image_paths[self.current_preview_index]
        
        if self.current_preview_index < len(self.image_animations):
            del self.image_animations[self.current_preview_index]
        
        # Update the preview index
        if self.images:
            self.current_preview_index = min(self.current_preview_index, len(self.images) - 1)
        else:
            self.current_preview_index = 0
        
        # Update the image list
        self.update_image_list()
        
        # Update the preview
        self.update_preview()
        self.update_ui_state()
    
    def update_ui_state(self):
        has_images = len(self.images) > 0
        
        # Enable/disable buttons based on state
        self.create_gif_button.configure(state="normal" if has_images else "disabled")
        self.prev_button.configure(state="normal" if has_images and len(self.images) > 1 else "disabled")
        self.next_button.configure(state="normal" if has_images and len(self.images) > 1 else "disabled")
        self.remove_button.configure(state="normal" if has_images else "disabled")
        self.apply_animation_button.configure(state="normal" if has_images else "disabled")
        self.apply_all_button.configure(state="normal" if has_images else "disabled")
    
    def create_gif(self):
        if not self.images:
            messagebox.showerror("Error", "No images to create GIF")
            return
        
        try:
            # Get settings
            duration = int(self.duration_entry.get())
            loop = int(self.loop_entry.get())
            transition_frames = int(self.frames_entry.get())
            
            if duration <= 0:
                messagebox.showerror("Error", "Duration must be greater than 0")
                return
            
            if transition_frames < 0:
                messagebox.showerror("Error", "Transition frames must be 0 or greater")
                return
                
        except ValueError:
            messagebox.showerror("Error", "Invalid duration, loop count, or transition frames")
            return
        
        # Ask user for save location
        save_path = filedialog.asksaveasfilename(
            title='Save GIF',
            defaultextension='.gif',
            filetypes=[('GIF files', '*.gif')],
            initialdir=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gif_maker", "output")
        )
        
        if not save_path:
            return
        
        self.status_label.configure(text="Status: Creating GIF...")
        
        # Run in a thread to avoid freezing UI
        threading.Thread(
            target=self._create_gif_thread, 
            args=(save_path, duration, loop, transition_frames), 
            daemon=True
        ).start()
    
    def create_transition_frames(self, prev_img, next_img, transition_type, num_frames):
        frames = []
        
        # Ensure both images are the same size
        if prev_img.size != next_img.size:
            next_img = next_img.resize(prev_img.size, Image.LANCZOS)
        
        width, height = prev_img.size
        
        # Skip transition if None or Instant is selected, or if num_frames is 0
        if transition_type == "None" or transition_type == "Instant" or num_frames == 0:
            return []
        
        if transition_type == "Fade in":
            # Create a series of images that gradually fade from prev to next
            for i in range(num_frames):
                alpha = i / num_frames
                frame = Image.blend(prev_img.convert("RGBA"), next_img.convert("RGBA"), alpha)
                frames.append(frame.convert("RGB") if frame.mode == "RGBA" else frame)
                
        elif transition_type == "Slide up":
            # Next image slides up from the bottom
            for i in range(num_frames):
                frame = Image.new("RGB", prev_img.size, (255, 255, 255))
                offset = int(height * (1 - i/num_frames))
                # Put the previous image fully visible
                frame.paste(prev_img, (0, 0))
                # Slide the next image up from the bottom
                visible_part = next_img.crop((0, 0, width, height - offset))
                frame.paste(visible_part, (0, offset))
                frames.append(frame)
        
        elif transition_type == "Slide down":
            # Next image slides down from the top
            for i in range(num_frames):
                frame = Image.new("RGB", prev_img.size, (255, 255, 255))
                offset = int(height * (i/num_frames))
                # Put the previous image fully visible
                frame.paste(prev_img, (0, 0))
                # Slide the next image down from the top
                visible_part = next_img.crop((0, offset, width, height))
                frame.paste(visible_part, (0, 0))
                frames.append(frame)
        
        elif transition_type == "Slide right":
            # Next image slides from the left
            for i in range(num_frames):
                frame = Image.new("RGB", prev_img.size, (255, 255, 255))
                offset = int(width * (1 - i/num_frames))
                # Put the previous image fully visible
                frame.paste(prev_img, (0, 0))
                # Slide the next image from the left
                visible_part = next_img.crop((0, 0, width - offset, height))
                frame.paste(visible_part, (offset, 0))
                frames.append(frame)
        
        elif transition_type == "Slide left":
            # Next image slides from the right
            for i in range(num_frames):
                frame = Image.new("RGB", prev_img.size, (255, 255, 255))
                offset = int(width * (i/num_frames))
                # Put the previous image fully visible
                frame.paste(prev_img, (0, 0))
                # Slide the next image from the right
                visible_part = next_img.crop((offset, 0, width, height))
                frame.paste(visible_part, (0, 0))
                frames.append(frame)
        
        elif transition_type == "Grow":
            # Next image grows from center
            for i in range(num_frames):
                frame = Image.new("RGB", prev_img.size, (255, 255, 255))
                scale = i / num_frames
                # Start with previous image
                frame.paste(prev_img, (0, 0))
                # Calculate the size and position of the growing image
                new_width = int(width * scale)
                new_height = int(height * scale)
                left = (width - new_width) // 2
                top = (height - new_height) // 2
                
                if new_width > 0 and new_height > 0:
                    growing_img = next_img.resize((new_width, new_height), Image.LANCZOS)
                    frame.paste(growing_img, (left, top))
                
                frames.append(frame)
        
        elif transition_type == "Shrink":
            # Previous image shrinks to center
            for i in range(num_frames):
                scale = 1 - (i / num_frames)
                
                # Create a blank frame with next image
                frame = Image.new("RGB", next_img.size, (255, 255, 255))
                frame.paste(next_img, (0, 0))
                
                # Calculate the size and position of the shrinking image
                new_width = max(1, int(width * scale))
                new_height = max(1, int(height * scale))
                left = (width - new_width) // 2
                top = (height - new_height) // 2
                
                if new_width > 0 and new_height > 0:
                    shrinking_img = prev_img.resize((new_width, new_height), Image.LANCZOS)
                    frame.paste(shrinking_img, (left, top))
                
                frames.append(frame)
                
        return frames
    
    def _create_gif_thread(self, save_path, duration, loop, transition_frames):
        try:
            # Resize all images to the same size (using the size of the first image)
            base_width, base_height = self.images[0].size
            resized_images = []
            
            for img in self.images:
                if img.size != (base_width, base_height):
                    resized = img.resize((base_width, base_height), Image.LANCZOS)
                    resized_images.append(resized)
                else:
                    resized_images.append(img.copy())
            
            # Create the final frames including transitions
            final_frames = []
            
            for i in range(len(resized_images)):
                # Add the current frame
                final_frames.append(resized_images[i])
                
                # Add transition to the next frame if it's not the last frame
                if i < len(resized_images) - 1:
                    # Get animation type for the current image
                    animation_type = self.image_animations[i] if i < len(self.image_animations) else "None"
                    
                    # Create transition frames
                    transition = self.create_transition_frames(
                        resized_images[i], 
                        resized_images[(i + 1) % len(resized_images)],
                        animation_type,
                        transition_frames
                    )
                    
                    # Add transition frames
                    final_frames.extend(transition)
            
            # Save as gif
            final_frames[0].save(
                save_path,
                format='GIF',
                append_images=final_frames[1:],
                save_all=True,
                duration=duration,
                loop=loop,
                optimize=False
            )
            
            self.root.after(0, lambda: self.status_label.configure(text=f"Status: GIF saved to {os.path.basename(save_path)}"))
            self.root.after(0, lambda: messagebox.showinfo("Success", f"GIF created successfully: {save_path}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to create GIF: {str(e)}"))
            self.root.after(0, lambda: self.status_label.configure(text="Status: Error creating GIF"))

if __name__ == "__main__":
    root = ctk.CTk()
    app = GifMakerApp(root)
    root.mainloop()
