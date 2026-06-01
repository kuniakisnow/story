# _plugins/ruby.rb
# Converts |base(reading) or |base（reading） to <ruby>base<rt>reading</rt></ruby>
# before Markdown rendering. This also prevents the pipe character from
# being interpreted as a table delimiter.

Jekyll::Hooks.register [:posts, :pages], :pre_render do |doc|
  doc.content.gsub!(/\|([^\|(（]+)[(（]([^)）]+)[)）]/) { "<ruby>#{$1}<rt>#{$2}</rt></ruby>" }
end
