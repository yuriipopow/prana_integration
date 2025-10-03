class Tools:
    @staticmethod
    def hex_string_to_int_list(hex_str: str) -> list[int]:
        # Remove spaces and make sure it's uppercase (optional)
        hex_str = hex_str.replace(" ", "").strip()
        
        # Split every 2 characters and convert to int
        return [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]
    
    